interface BrandMarkProps {
  compact?: boolean;
}

export function BrandMark({ compact = false }: BrandMarkProps) {
  if (compact) {
    return (
      <div className="brand-mark brand-mark--compact" aria-label="Buxme AI-Scout">
        <img className="brand-mark__image" src="/brand/buxme-logo-header.png" alt="" />
      </div>
    );
  }

  return (
    <div className="brand-mark" aria-label="Buxme AI-Scout">
      <span className="brand-mark__b">BU</span>
      <span className="brand-mark__x">X</span>
      <span className="brand-mark__me">ME</span>
    </div>
  );
}
