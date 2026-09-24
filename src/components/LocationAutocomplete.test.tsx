import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { describe, expect, it } from 'vitest';
import { suggestLocations } from '../data/locations';
import { LocationAutocomplete } from './LocationAutocomplete';

function Example() {
  const [value, setValue] = useState('');
  return <LocationAutocomplete value={value} onChange={setValue} />;
}

describe('location suggestions', () => {
  it('includes cities and regions for a prefix', () => {
    const names = suggestLocations('Са').map(({ name }) => name);
    expect(names).toContain('Самара');
    expect(names).toContain('Саратов');
    expect(names).toContain('Самарская область');
  });

  it('matches ё and е and keeps same-name cities distinguishable', () => {
    expect(suggestLocations('орел').some(({ name }) => name === 'Орёл')).toBe(true);
    const kirovs = suggestLocations('Киров', 20).filter(({ name }) => name === 'Киров');
    expect(new Set(kirovs.map(({ region }) => region)).size).toBe(2);
  });

  it('supports keyboard selection without submitting the form', async () => {
    const user = userEvent.setup();
    render(<Example />);
    const input = screen.getByRole('combobox');
    await user.type(input, 'Самар');
    expect(screen.getByRole('listbox')).toBeInTheDocument();
    await user.keyboard('{ArrowDown}{Enter}');
    expect(input).toHaveValue('Самара');
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });
});
