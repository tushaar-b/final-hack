import React, { useEffect, useRef } from 'react';
import Matter from 'matter-js';

export default function BhaluPhysics() {
  const containerRef = useRef(null);
  
  // Arrays for multiple mascots
  const mascotRefs = useRef([]);
  const bodiesRef = useRef([]);
  const draggingId = useRef(null);

  const mascots = [
    { id: 'bear', src: '/BHALU.png', startX: -50 },
    { id: 'bull', src: '/Bull.png', startX: 50 }
  ];

  useEffect(() => {
    if (!containerRef.current || mascotRefs.current.length === 0) return;

    const { Engine, Runner, Bodies, Composite } = Matter;
    
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    const engine = Engine.create();
    const radius = 75; // 150px / 2
    
    // Create bodies
    const newBodies = mascots.map((m) => {
      return Bodies.circle(width / 2 + m.startX, 80, radius, {
        restitution: 0.9,
        frictionAir: 0.005,
        density: 0.05,
        friction: 0.1
      });
    });
    bodiesRef.current = newBodies;

    // Create walls (thickness 50)
    const wallOptions = { isStatic: true };
    const ground = Bodies.rectangle(width / 2, height + 25, width, 50, wallOptions);
    const leftWall = Bodies.rectangle(-25, height / 2, 50, height, wallOptions);
    const rightWall = Bodies.rectangle(width + 25, height / 2, 50, height, wallOptions);
    const ceiling = Bodies.rectangle(width / 2, -25, width, 50, wallOptions);

    Composite.add(engine.world, [...newBodies, ground, leftWall, rightWall, ceiling]);

    const runner = Runner.create();
    Runner.run(runner, engine);

    // Sync bodies to DOM
    let animationFrame;
    const update = () => {
      newBodies.forEach((body, idx) => {
        const domEl = mascotRefs.current[idx];
        if (domEl && body) {
          const { x, y } = body.position;
          const angle = body.angle;
          domEl.style.transform = `translate(${x - radius}px, ${y - radius}px) rotate(${angle}rad)`;
        }
      });
      animationFrame = requestAnimationFrame(update);
    };
    update();

    // Handle container resize
    const resizeObs = new ResizeObserver((entries) => {
      const { width: w, height: h } = entries[0].contentRect;
      Matter.Body.setPosition(ground, { x: w / 2, y: h + 25 });
      Matter.Body.setPosition(rightWall, { x: w + 25, y: h / 2 });
      Matter.Body.setPosition(ceiling, { x: w / 2, y: -25 });
      
      newBodies.forEach((body) => {
        if (body.position.y > h) {
           Matter.Body.setPosition(body, { x: w / 2, y: h / 2 });
           Matter.Body.setVelocity(body, { x: 0, y: 0 });
        }
      });
    });
    resizeObs.observe(containerRef.current);

    return () => {
      cancelAnimationFrame(animationFrame);
      resizeObs.disconnect();
      Runner.stop(runner);
      Engine.clear(engine);
    };
  }, []);

  const handlePointerDown = (e, index) => {
    draggingId.current = index;
    e.target.setPointerCapture(e.pointerId);
  };
  
  const handlePointerMove = (e) => {
    const idx = draggingId.current;
    if (idx === null || !bodiesRef.current[idx]) return;
    
    const body = bodiesRef.current[idx];
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const dx = x - body.position.x;
    const dy = y - body.position.y;
    
    Matter.Body.setPosition(body, { x, y });
    Matter.Body.setVelocity(body, { x: dx * 0.7, y: dy * 0.7 });
  };

  const handlePointerUp = (e) => {
    draggingId.current = null;
    e.target.releasePointerCapture(e.pointerId);
  };

  return (
    <div ref={containerRef} className="absolute inset-0 z-20 pointer-events-none overflow-hidden">
      {mascots.map((m, i) => (
        <img
          key={m.id}
          ref={(el) => (mascotRefs.current[i] = el)}
          src={m.src}
          alt={m.id}
          className="absolute top-0 left-0 w-[150px] h-[150px] object-contain cursor-grab active:cursor-grabbing pointer-events-auto"
          style={{ 
            touchAction: 'none',
            filter: 'drop-shadow(0px 10px 15px rgba(0,0,0,0.5))'
          }}
          onPointerDown={(e) => handlePointerDown(e, i)}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
        />
      ))}
    </div>
  );
}
