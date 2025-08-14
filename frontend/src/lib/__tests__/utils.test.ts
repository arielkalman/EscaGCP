import { cn, formatNumber } from '../utils';

describe('cn utility function', () => {
  it('should merge class names correctly', () => {
    expect(cn('bg-red-500', 'text-white')).toBe('bg-red-500 text-white');
  });

  it('should handle conditional classes', () => {
    expect(cn('bg-red-500', true && 'text-white', false && 'hidden')).toBe('bg-red-500 text-white');
  });

  it('should handle undefined and null values', () => {
    expect(cn('bg-red-500', undefined, null, 'text-white')).toBe('bg-red-500 text-white');
  });

  it('should handle Tailwind CSS conflicts with twMerge', () => {
    expect(cn('px-2 py-1 px-3')).toBe('py-1 px-3');
  });

  it('should handle array of classes', () => {
    expect(cn(['bg-red-500', 'text-white'])).toBe('bg-red-500 text-white');
  });

  it('should handle empty input', () => {
    expect(cn()).toBe('');
  });

  it('should handle object with boolean values', () => {
    expect(cn({
      'bg-red-500': true,
      'text-white': false,
      'border': true
    })).toBe('bg-red-500 border');
  });
});

describe('formatNumber utility function', () => {
  it('should format numbers less than 1000 as-is', () => {
    expect(formatNumber(0)).toBe('0');
    expect(formatNumber(1)).toBe('1');
    expect(formatNumber(999)).toBe('999');
  });

  it('should format thousands with K suffix', () => {
    expect(formatNumber(1000)).toBe('1.0K');
    expect(formatNumber(1500)).toBe('1.5K');
    expect(formatNumber(2000)).toBe('2.0K');
    expect(formatNumber(15000)).toBe('15.0K');
    expect(formatNumber(999999)).toBe('1000.0K');
  });

  it('should format millions with M suffix', () => {
    expect(formatNumber(1000000)).toBe('1.0M');
    expect(formatNumber(1500000)).toBe('1.5M');
    expect(formatNumber(2000000)).toBe('2.0M');
    expect(formatNumber(15000000)).toBe('15.0M');
  });

  it('should handle decimal places correctly', () => {
    expect(formatNumber(1234)).toBe('1.2K');
    expect(formatNumber(1678)).toBe('1.7K');
    expect(formatNumber(1234567)).toBe('1.2M');
    expect(formatNumber(1678900)).toBe('1.7M');
  });

  it('should handle edge cases', () => {
    expect(formatNumber(999.9)).toBe('999.9');
    expect(formatNumber(1000.1)).toBe('1.0K');
    expect(formatNumber(999999.9)).toBe('1000.0K');
    expect(formatNumber(1000000.1)).toBe('1.0M');
  });

  it('should handle large numbers', () => {
    expect(formatNumber(1000000000)).toBe('1000.0M');
    expect(formatNumber(999999999)).toBe('1000.0M');
  });
}); 