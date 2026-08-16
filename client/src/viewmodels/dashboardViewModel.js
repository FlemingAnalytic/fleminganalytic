import { useState } from 'react';

export const useDashboardViewModel = () => {
  const [cardLayout, setCardLayout] = useState('grid'); // 'grid' | 'list' | 'compact'

  const toggleLayout = () => {
    setCardLayout(prev => {
      if (prev === 'grid') return 'list';
      if (prev === 'list') return 'compact';
      return 'grid';
    });
  };

  return { cardLayout, toggleLayout };
};
