import type { AIScore } from '../types/scout';

export function ScoreBadge({ score, large = false }: { score: AIScore; large?: boolean }) {
  return (
    <div className={`score-badge score-badge--${score.level} ${large ? 'score-badge--large' : ''}`}>
      <strong>{score.value}%</strong>
      <span>{score.label}</span>
    </div>
  );
}
