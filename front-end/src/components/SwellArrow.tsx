// components/SwellArrow.tsx
import { ArrowUp } from 'lucide-react';

interface SwellArrowProps {
  direction: number;
}

export function SwellArrow({ direction }: SwellArrowProps) {
  const arrowRotation = 360 - direction;
  return (
    <div
      className="inline-block transform"
      style={{ transform: `rotate(${arrowRotation}deg)` }}
      title={`Swell from ${direction}°`}
    >
      <ArrowUp className="w-4 h-4 text-white inline" />
    </div>
  );
}
