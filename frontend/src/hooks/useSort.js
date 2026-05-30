import { useState, useMemo, useCallback } from 'react';

export function useSort(defaultKey = 'returns', defaultDir = 'desc') {
  const [sort, setSort] = useState({ key: defaultKey, dir: defaultDir });

  const onSort = useCallback((key) => {
    setSort(prev => ({
      key,
      dir: prev.key === key && prev.dir === 'desc' ? 'asc' : 'desc'
    }));
  }, []);

  const sorter = useMemo(() => {
    const { key, dir } = sort;
    return (a, b) => {
      let av = a[key];
      let bv = b[key];
      if (av == null && bv == null) return 0;
      if (av == null) return dir === 'desc' ? -1 : 1;
      if (bv == null) return dir === 'desc' ? 1 : -1;
      if (typeof av === 'string') av = av.toLowerCase();
      if (typeof bv === 'string') bv = bv.toLowerCase();
      if (av < bv) return dir === 'desc' ? 1 : -1;
      if (av > bv) return dir === 'desc' ? -1 : 1;
      return 0;
    };
  }, [sort]);

  return { sort, onSort, sorter };
}
