import data from './russian-locations.json';

export type LocationSuggestion = {
  id: string;
  name: string;
  region?: string;
  kind: 'city' | 'region';
  population: number;
};

const normalize = (value: string) => value.toLocaleLowerCase('ru').replaceAll('ё', 'е').trim();

const locations: LocationSuggestion[] = [
  ...data.regions.map((name) => ({ id: `region:${name}`, name, kind: 'region' as const, population: 0 })),
  ...data.cities.map(([name, region, population]) => ({
    id: `city:${name}:${region}`,
    name: String(name),
    region: String(region),
    kind: 'city' as const,
    population: Number(population),
  })),
];

export function suggestLocations(query: string, limit = 8): LocationSuggestion[] {
  const normalized = normalize(query);
  if (!normalized) return [];

  const matches = locations
    .filter(({ name, region, kind }) => {
      const regionName = region ?? name;
      return normalize(name).startsWith(normalized)
        || normalize(regionName).startsWith(normalized)
        || (kind === 'region' && normalize(name.replace(/^(республика|город)\s+/i, '')).startsWith(normalized));
    })
    .sort((a, b) => {
      const aNameMatch = normalize(a.name).startsWith(normalized);
      const bNameMatch = normalize(b.name).startsWith(normalized);
      if (aNameMatch !== bNameMatch) return aNameMatch ? -1 : 1;
      if (a.kind !== b.kind) return a.kind === 'city' ? -1 : 1;
      if (a.population !== b.population) return b.population - a.population;
      return a.name.localeCompare(b.name, 'ru');
    })
  const cities = matches.filter(({ kind }) => kind === 'city');
  const regions = matches.filter(({ kind }) => kind === 'region');
  const firstCities = Math.max(4, limit - regions.length);
  return [...cities.slice(0, firstCities), ...regions, ...cities.slice(firstCities)].slice(0, limit);
}
