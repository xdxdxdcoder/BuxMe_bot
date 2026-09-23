interface BrandMarkProps {
  compact?: boolean;
}

export function BrandMark({ compact = false }: BrandMarkProps) {
  return (
    <div className={`brand-mark ${compact ? 'brand-mark--compact' : ''}`} aria-label="Buxme AI-Scout">
      <span className="brand-mark__b">BU</span>
      <span className="brand-mark__x">X</span>
      <span className="brand-mark__me">ME</span>
    </div>
  );
}
