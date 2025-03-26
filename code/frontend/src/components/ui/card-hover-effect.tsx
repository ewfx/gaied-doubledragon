import { cn } from "../../utils/cn";
import { AnimatePresence, motion } from "framer-motion";
import { useState, useEffect, useCallback } from "react";

export const HoverEffect = ({
  items,
  className,
}: {
  items: {
    icon?: React.ReactNode;
    title: string;
    description: string;
    onClick?: () => void;
  }[];
  className?: string;
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [touchStart, setTouchStart] = useState(0);
  const [touchEnd, setTouchEnd] = useState(0);

  const handleNext = useCallback(() => {
    setCurrentIndex((prevIndex) => (prevIndex + 1) % items.length);
  }, [items.length]);

  const handlePrev = useCallback(() => {
    setCurrentIndex((prevIndex) => (prevIndex - 1 + items.length) % items.length);
  }, [items.length]);

  // Auto-advance timer
  useEffect(() => {
    const timer = setInterval(handleNext, 5000);
    return () => clearInterval(timer);
  }, [handleNext]);

  // Touch handlers
  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.targetTouches[0].clientX);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const handleTouchEnd = () => {
    if (touchStart - touchEnd > 50) {
      handleNext();
    }
    if (touchStart - touchEnd < -50) {
      handlePrev();
    }
  };

  const handleClick = () => {
    // Safely check if the current item has an onClick handler
    const currentItem = items[currentIndex];
    if (currentItem && typeof currentItem.onClick === 'function') {
      currentItem.onClick();
    }
  };

  // Ensure we have a valid currentIndex
  const safeCurrentIndex = items && items.length > 0 
    ? currentIndex % items.length 
    : 0;

  // Safely get the current item
  const currentItem = items && items.length > 0 
    ? items[safeCurrentIndex] 
    : { title: '', description: '' };

  return (
    <div className={cn("relative", className)}>
      <div
        role="region"
        aria-label="Carousel"
        className="overflow-hidden"
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={safeCurrentIndex}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
            className="relative group block p-2 h-full w-full"
            role="button"
            onClick={handleClick}
            style={{ cursor: currentItem.onClick ? 'pointer' : 'default' }}
          >
            <div className="rounded-2xl h-full w-full p-4 overflow-hidden bg-zinc-900 border border-zinc-800 relative z-20">
              <div className="relative z-50">
                {/* Only render icon if it exists */}
                {currentItem.icon && (
                  <div className="p-4">{currentItem.icon}</div>
                )}
                <div className="p-4">
                  <div className="text-zinc-100 font-semibold tracking-wide">
                    {currentItem.title}
                  </div>
                  <div className="mt-2 text-zinc-400 tracking-wide leading-relaxed text-sm">
                    {currentItem.description}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation dots */}
      <div className="absolute inset-x-0 bottom-2 flex justify-center gap-2 z-50">
        {items.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentIndex(index)}
            className={`w-2 h-2 rounded-full transition-all duration-300 ${
              index === safeCurrentIndex
                ? "bg-indigo-500 w-4"
                : "bg-zinc-600 hover:bg-zinc-500"
            }`}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
};
