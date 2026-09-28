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
      body: `Предлагаем пилот Buxme для прозрачного управления полевой командой ${company.industry.toLowerCase()}. За 14 дней настроим маршруты, контроль визитов и понятную аналитику без изменения привычных процессов менеджеров.`,
    };
  }
  return {
    title: 'Скрипт первого контакта',
    body: `Добрый день! Я изучил работу «${company.name}» и увидел, что ваша команда активно работает по региону. Buxme помогает руководителям видеть визиты и результаты полевых сотрудников в одном окне. Подскажите, как сейчас вы контролируете работу команды вне офиса?`,
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
