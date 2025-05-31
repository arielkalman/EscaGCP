import React from 'react';
import { render } from '@/test/utils/testUtils';
import { LoadingSpinner } from '../LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders loading spinner icon', () => {
    const { container } = render(<LoadingSpinner />);
    const spinnerIcon = container.querySelector('svg');
    expect(spinnerIcon).toBeInTheDocument();
    expect(spinnerIcon).toHaveClass('animate-spin');
  });

  it('renders without text by default', () => {
    const { container } = render(<LoadingSpinner />);
    const textElement = container.querySelector('p');
    expect(textElement).not.toBeInTheDocument();
  });

  it('renders with small size class', () => {
    const { container } = render(<LoadingSpinner size="sm" />);
    const spinner = container.querySelector('svg');
    expect(spinner).toHaveClass('h-4', 'w-4');
  });

  it('renders with large size class', () => {
    const { container } = render(<LoadingSpinner size="lg" />);
    const spinner = container.querySelector('svg');
    expect(spinner).toHaveClass('h-8', 'w-8');
  });

  it('has default medium size when no size specified', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.querySelector('svg');
    expect(spinner).toHaveClass('h-6', 'w-6');
  });

  it('displays custom text when provided', () => {
    const loadingText = 'Please wait...';
    const { getByText } = render(<LoadingSpinner text={loadingText} />);
    expect(getByText(loadingText)).toBeInTheDocument();
  });

  it('applies custom className correctly', () => {
    const customClass = 'my-custom-class';
    const { container } = render(<LoadingSpinner className={customClass} />);
    expect(container.firstChild).toHaveClass(customClass);
  });

  it('combines custom className with default classes', () => {
    const customClass = 'extra-spacing';
    const { container } = render(<LoadingSpinner className={customClass} />);
    const element = container.firstChild as HTMLElement;
    expect(element).toHaveClass(customClass);
    expect(element).toHaveClass('flex');
    expect(element).toHaveClass('items-center');
  });

  it('renders spinner icon with animation', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('shows loading text with proper spacing when provided', () => {
    const loadingText = 'Processing...';
    const { getByText } = render(<LoadingSpinner text={loadingText} />);
    const textElement = getByText(loadingText);
    expect(textElement).toBeInTheDocument();
    expect(textElement).toHaveClass('mt-2', 'text-sm', 'text-muted-foreground');
  });

  it('has proper text styling when text is provided', () => {
    const loadingText = 'Loading data...';
    const { getByText } = render(<LoadingSpinner text={loadingText} />);
    const textElement = getByText(loadingText);
    expect(textElement.tagName).toBe('P');
    expect(textElement).toHaveClass('mt-2', 'text-sm', 'text-muted-foreground');
  });

  // Performance and edge case tests
  describe('Performance and Edge Cases', () => {
    it('renders quickly with minimal DOM elements', () => {
      const { container } = render(<LoadingSpinner />);
      const allElements = container.querySelectorAll('*');
      expect(allElements.length).toBeLessThan(5); // Should be lightweight
    });

    // Test different size variations
    (['sm', 'md', 'lg'] as const).forEach((size) => {
      it(`renders correctly with ${size} size`, () => {
        const { container } = render(<LoadingSpinner size={size} />);
        const sizeClassMap = {
          sm: 'h-4 w-4',
          md: 'h-6 w-6',
          lg: 'h-8 w-8'
        };
        const expectedClasses = sizeClassMap[size].split(' ');
        const spinner = container.querySelector('svg');
        expectedClasses.forEach(className => {
          expect(spinner).toHaveClass(className);
        });
      });
    });

    it('handles empty text by not rendering text element', () => {
      const { container } = render(<LoadingSpinner text="" />);
      const textElement = container.querySelector('p');
      expect(textElement).not.toBeInTheDocument();
    });

    it('handles very long text without breaking layout', () => {
      const longText = 'This is a very long loading message that should not break the layout or cause overflow issues';
      const { getByText } = render(<LoadingSpinner text={longText} />);
      expect(getByText(longText)).toBeInTheDocument();
    });

    it('handles special characters in text', () => {
      const specialText = 'Loading... 🚀 100% & more!';
      const { getByText } = render(<LoadingSpinner text={specialText} />);
      expect(getByText(specialText)).toBeInTheDocument();
    });

    it('renders proper icon structure', () => {
      const { container } = render(<LoadingSpinner />);
      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('fill', 'none');
      expect(svg).toHaveClass('text-primary');
    });
  });
}); 