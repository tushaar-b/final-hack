import React, { useEffect, useRef } from 'react';
import Matter from 'matter-js';

export default function BhaluPhysics() {
  const containerRef = useRef(null);
  const bearRef = useRef(null);
  const bodyRef = useRef(null);
  const isDragging = useRef(false);

  useEffect(() => {
    if (!containerRef.current || !bearRef.current) return;

    const { Engine, Runner, Bodies, Composite } = Matter;
    
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    const engine = Engine.create();
    
    // Bear size
    const radius = 40; // 80px / 2
    
    // Create bear body
    const bear = Bodies.circle(width / 2, 50, radius, {
      restitution: 0.9, // Very bouncy
      frictionAir: 0.01,
      density: 0.05,
      friction: 0.1
    });
    bodyRef.current = bear;

    // Create walls (thickness 50)
    const wallOptions = { isStatic: true };
    const ground = Bodies.rectangle(width / 2, height + 25, width, 50, wallOptions);
    const leftWall = Bodies.rectangle(-25, height / 2, 50, height, wallOptions);
    const rightWall = Bodies.rectangle(width + 25, height / 2, 50, height, wallOptions);
    const ceiling = Bodies.rectangle(width / 2, -25, width, 50, wallOptions);

    Composite.add(engine.world, [bear, ground, leftWall, rightWall, ceiling]);

    const runner = Runner.create();
    Runner.run(runner, engine);

    // Sync body to DOM
    let animationFrame;
    const update = () => {
      if (bearRef.current && bodyRef.current) {
        const { x, y } = bodyRef.current.position;
        const angle = bodyRef.current.angle;
        // Position it by top-left for translate
        bearRef.current.style.transform = `translate(${x - radius}px, ${y - radius}px) rotate(${angle}rad)`;
      }
      animationFrame = requestAnimationFrame(update);
    };
    update();

    // Handle container resize
    const resizeObs = new ResizeObserver((entries) => {
      const { width: w, height: h } = entries[0].contentRect;
      Matter.Body.setPosition(ground, { x: w / 2, y: h + 25 });
      Matter.Body.setPosition(rightWall, { x: w + 25, y: h / 2 });
      Matter.Body.setPosition(ceiling, { x: w / 2, y: -25 });
      // Keep bear in bounds if container shrinks
      if (bodyRef.current.position.y > h) {
         Matter.Body.setPosition(bodyRef.current, { x: w / 2, y: h / 2 });
         Matter.Body.setVelocity(bodyRef.current, { x: 0, y: 0 });
      }
    });
    resizeObs.observe(containerRef.current);

    return () => {
      cancelAnimationFrame(animationFrame);
      resizeObs.disconnect();
      Runner.stop(runner);
      Engine.clear(engine);
    };
  }, []);

  const handlePointerDown = (e) => {
    isDragging.current = true;
    e.target.setPointerCapture(e.pointerId);
  };
  
  const handlePointerMove = (e) => {
    if (!isDragging.current || !bodyRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    Matter.Body.setPosition(bodyRef.current, { x, y });
    Matter.Body.setVelocity(bodyRef.current, { x: e.movementX, y: e.movementY });
  };

  const handlePointerUp = (e) => {
    isDragging.current = false;
    e.target.releasePointerCapture(e.pointerId);
  };

  return (
    <div ref={containerRef} className="absolute inset-0 z-20 pointer-events-none overflow-hidden">
      <img
        ref={bearRef}
        src="/BHALU.png"
        alt="Bhalu"
        className="absolute top-0 left-0 w-[80px] h-[80px] object-contain cursor-grab active:cursor-grabbing pointer-events-auto"
        style={{ 
          touchAction: 'none',
          filter: 'drop-shadow(0px 10px 15px rgba(0,0,0,0.5))'
        }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      />
    </div>
  );
}
