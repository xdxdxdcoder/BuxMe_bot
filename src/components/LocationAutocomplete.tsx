import { useId, useState, type KeyboardEvent } from 'react';
import { suggestLocations } from '../data/locations';

type Props = {
  value: string;
  onChange: (value: string) => void;
};

export function LocationAutocomplete({ value, onChange }: Props) {
  const listId = useId();
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const suggestions = suggestLocations(value);
  const visible = open && suggestions.length > 0;

  const select = (index: number) => {
    onChange(suggestions[index].name);
    setOpen(false);
    setActiveIndex(-1);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Escape') {
      setOpen(false);
      setActiveIndex(-1);
      return;
    }
    if (!visible) return;
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex((current) => event.key === 'ArrowDown'
        ? (current + 1) % suggestions.length
        : (current - 1 + suggestions.length) % suggestions.length);
    } else if (event.key === 'Enter' && activeIndex >= 0) {
      event.preventDefault();
      select(activeIndex);
    }
  };

  return (
    <div className="location-autocomplete" onBlur={(event) => {
      if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
    }}>
      <input
        id="region"
        autoComplete="off"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={visible}
        aria-controls={visible ? listId : undefined}
        aria-activedescendant={visible && activeIndex >= 0 ? `${listId}-${activeIndex}` : undefined}
        placeholder="Например, Краснодарский край"
        value={value}
        onChange={(event) => { onChange(event.target.value); setOpen(true); setActiveIndex(-1); }}
        onFocus={() => setOpen(true)}
        onKeyDown={handleKeyDown}
      />
      {visible ? (
        <div className="location-autocomplete__list" id={listId} role="listbox" aria-label="Подсказки городов и регионов">
          {suggestions.map((item, index) => (
            <button
              id={`${listId}-${index}`}
              key={item.id}
              role="option"
              aria-selected={index === activeIndex}
              className={`location-autocomplete__option ${index === activeIndex ? 'is-active' : ''}`}
              type="button"
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => select(index)}
            >
              <span>{item.name}</span>
              <small>{item.kind === 'city' ? item.region : 'Регион'}</small>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
