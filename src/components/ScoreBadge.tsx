import type { AIScore } from '../types/scout';

export function ScoreBadge({ score, large = false }: { score: AIScore; large?: boolean }) {
  return (
    <div className={`score-badge score-badge--${score.level} ${large ? 'score-badge--large' : ''}`}>
      <strong>{score.value}<small>/100</small></strong>
      <span>{score.label}</span>
    </div>
  );
}
