import type { Company, ContactResult, GeneratedContent, ScoreRecalculation } from '../../types/scout';

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

export async function generateCompanyContent(
  company: Company,
  kind: 'offer' | 'script',
): Promise<GeneratedContent> {
  await wait(900);
  if (kind === 'offer') {
    return {
      title: `Оффер для «${company.name}»`,
      body: `Здравствуйте! Мы рассматриваем «${company.name}» как возможного партнёра в сфере ${company.industry.toLowerCase()}. Если у вас есть сотрудники, которые работают вне офиса, можем обсудить пилот Buxme для планирования визитов и анализа результатов. Подскажите, актуальна ли такая задача?`,
    };
  }
  return {
    title: 'Скрипт первого контакта',
    body: `Добрый день! Меня зовут [имя], я из Buxme. Хотел уточнить, есть ли у «${company.name}» сотрудники, которые регулярно работают вне офиса и посещают клиентов. Если да, как вы сейчас планируете их визиты и оцениваете результаты?`,
  };
}

export async function recalculateScore(
  company: Company,
  result: ContactResult,
): Promise<ScoreRecalculation> {
  await wait(950);
  const weights = [result.reachedDecisionMaker, result.hasFieldTeam, result.automationInterest].reduce(
    (sum, value) => sum + (value === 'yes' ? 5 : value === 'no' ? -7 : 0),
    0,
  );
  const newScore = Math.max(0, Math.min(100, company.score.value + weights));
  return {
    previousScore: company.score.value,
    newScore,
    delta: newScore - company.score.value,
    explanation: newScore >= company.score.value
      ? 'Ответы подтвердили коммерческий потенциал и наличие подходящей полевой команды.'
      : 'После контакта часть исходных сигналов не подтвердилась — приоритет снижен.',
  };
}
