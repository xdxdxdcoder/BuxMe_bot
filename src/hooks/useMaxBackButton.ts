import { useEffect } from 'react';
import { maxBridge } from '../services/max/maxBridge';

export function useMaxBackButton(handler: (() => void) | null) {
  useEffect(() => maxBridge.setBackHandler(handler), [handler]);
}
