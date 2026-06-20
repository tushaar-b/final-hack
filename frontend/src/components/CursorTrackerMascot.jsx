import React, { useEffect } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';

export default function CursorTrackerMascot({ className = "" }) {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  useEffect(() => {
    const handleMouseMove = (e) => {
      const { innerWidth, innerHeight } = window;
      const x = (e.clientX / innerWidth - 0.5) * 2; 
      const y = (e.clientY / innerHeight - 0.5) * 2; 
      
      mouseX.set(x);
      mouseY.set(y);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [mouseX, mouseY]);

  const springConfig = { damping: 30, stiffness: 120, mass: 1 };
  const smoothX = useSpring(mouseX, springConfig);
  const smoothY = useSpring(mouseY, springConfig);

  const rotateX = useTransform(smoothY, [-1, 1], [12, -12]); 
  const rotateY = useTransform(smoothX, [-1, 1], [-20, 20]); 
  const translateX = useTransform(smoothX, [-1, 1], [-8, 8]); 

  return (
    <div 
      className={`relative ${className}`}
      style={{ perspective: 1200 }}
    >
      <motion.div
        className="w-full h-full origin-center"
        style={{
          rotateX,
          rotateY,
          x: translateX,
          transformStyle: "preserve-3d"
        }}
      >
        <motion.div
          animate={{ y: [0, -6, 0] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          className="w-full h-full pointer-events-none"
        >
          <img 
            src="/bear-mascot.png" 
            alt="Aarthi AI Bear Mascot" 
            className="w-full h-full object-contain pointer-events-none"
            style={{ 
              filter: 'drop-shadow(0 20px 25px rgba(0,0,0,0.8)) drop-shadow(0 0 15px rgba(212,175,55,0.2))'
            }}
          />
        </motion.div>
      </motion.div>
    </div>
  );
}
