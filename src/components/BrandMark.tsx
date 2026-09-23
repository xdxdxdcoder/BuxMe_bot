interface BrandMarkProps {
  compact?: boolean;
}

export function BrandMark({ compact = false }: BrandMarkProps) {
  return (
    <div className={`brand-mark ${compact ? 'brand-mark--compact' : ''}`} aria-label="Buxme AI-Scout">
      <img className="brand-mark__image" src="/brand/buxme-logo-header.png" alt="" />
    </div>
  );
}
