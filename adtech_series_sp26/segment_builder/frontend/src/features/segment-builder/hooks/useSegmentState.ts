/**
 * Reducer hook for segment state management.
 */

import { useReducer, useCallback } from 'react';
import type {
  SegmentState,
  SegmentAction,
  SegmentDefinition,
  SegmentCondition,
  LogicType,
  ModeType,
  SegmentPreview,
  ChatMessage,
} from '../types';

const generateId = () => crypto.randomUUID().slice(0, 8);

const createEmptyCondition = (): SegmentCondition => ({
  id: generateId(),
  feature: '',
  operator: 'IS',
  values: [],
});

const createEmptyGroup = () => ({
  id: generateId(),
  logic: 'AND' as LogicType,
  conditions: [createEmptyCondition()],
});

const initialSegment: SegmentDefinition = {
  name: '',
  description: '',
  groups: [createEmptyGroup()],
  groupLogic: 'AND',
};

const initialState: SegmentState = {
  mode: 'agent',
  segment: initialSegment,
  preview: null,
  isLoading: false,
  error: null,
  chatHistory: [],
};

export function segmentReducer(state: SegmentState, action: SegmentAction): SegmentState {
  switch (action.type) {
    case 'SET_MODE':
      return { ...state, mode: action.payload };

    case 'SET_SEGMENT':
      return { ...state, segment: action.payload };

    case 'ADD_GROUP':
      return {
        ...state,
        segment: {
          ...state.segment,
          groups: [...state.segment.groups, createEmptyGroup()],
        },
      };

    case 'REMOVE_GROUP':
      return {
        ...state,
        segment: {
          ...state.segment,
          groups: state.segment.groups.filter((g) => g.id !== action.payload),
        },
      };

    case 'SET_GROUP_LOGIC':
      return {
        ...state,
        segment: {
          ...state.segment,
          groups: state.segment.groups.map((g) =>
            g.id === action.payload.groupId ? { ...g, logic: action.payload.logic } : g
          ),
        },
      };

    case 'ADD_CONDITION':
      return {
        ...state,
        segment: {
          ...state.segment,
          groups: state.segment.groups.map((g) =>
            g.id === action.payload.groupId
              ? { ...g, conditions: [...g.conditions, createEmptyCondition()] }
              : g
          ),
        },
      };

    case 'UPDATE_CONDITION':
      return {
        ...state,
        segment: {
          ...state.segment,
          groups: state.segment.groups.map((g) =>
            g.id === action.payload.groupId
              ? {
                  ...g,
                  conditions: g.conditions.map((c) =>
                    c.id === action.payload.condition.id ? action.payload.condition : c
                  ),
                }
              : g
          ),
        },
      };

    case 'REMOVE_CONDITION':
      return {
        ...state,
        segment: {
          ...state.segment,
          groups: state.segment.groups.map((g) =>
            g.id === action.payload.groupId
              ? {
                  ...g,
                  conditions: g.conditions.filter((c) => c.id !== action.payload.conditionId),
                }
              : g
          ),
        },
      };

    case 'SET_PREVIEW':
      return { ...state, preview: action.payload };

    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload };

    case 'ADD_CHAT_MESSAGE':
      return { ...state, chatHistory: [...state.chatHistory, action.payload] };

    case 'CLEAR_CHAT':
      return { ...state, chatHistory: [] };

    case 'RESET_SEGMENT':
      return { ...state, segment: initialSegment, preview: null };

    case 'SET_SEGMENT_GROUP_LOGIC':
      return {
        ...state,
        segment: {
          ...state.segment,
          groupLogic: action.payload,
        },
      };

    default:
      return state;
  }
}

export function useSegmentState() {
  const [state, dispatch] = useReducer(segmentReducer, initialState);

  const setMode = useCallback((mode: ModeType) => {
    dispatch({ type: 'SET_MODE', payload: mode });
  }, []);

  const setSegment = useCallback((segment: SegmentDefinition) => {
    dispatch({ type: 'SET_SEGMENT', payload: segment });
  }, []);

  const addGroup = useCallback(() => {
    dispatch({ type: 'ADD_GROUP' });
  }, []);

  const removeGroup = useCallback((groupId: string) => {
    dispatch({ type: 'REMOVE_GROUP', payload: groupId });
  }, []);

  const setGroupLogic = useCallback((groupId: string, logic: LogicType) => {
    dispatch({ type: 'SET_GROUP_LOGIC', payload: { groupId, logic } });
  }, []);

  const addCondition = useCallback((groupId: string) => {
    dispatch({ type: 'ADD_CONDITION', payload: { groupId } });
  }, []);

  const updateCondition = useCallback((groupId: string, condition: SegmentCondition) => {
    dispatch({ type: 'UPDATE_CONDITION', payload: { groupId, condition } });
  }, []);

  const removeCondition = useCallback((groupId: string, conditionId: string) => {
    dispatch({ type: 'REMOVE_CONDITION', payload: { groupId, conditionId } });
  }, []);

  const setPreview = useCallback((preview: SegmentPreview | null) => {
    dispatch({ type: 'SET_PREVIEW', payload: preview });
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  }, []);

  const setError = useCallback((error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  }, []);

  const addChatMessage = useCallback((message: ChatMessage) => {
    dispatch({ type: 'ADD_CHAT_MESSAGE', payload: message });
  }, []);

  const clearChat = useCallback(() => {
    dispatch({ type: 'CLEAR_CHAT' });
  }, []);

  const resetSegment = useCallback(() => {
    dispatch({ type: 'RESET_SEGMENT' });
  }, []);

  const setSegmentGroupLogic = useCallback((logic: LogicType) => {
    dispatch({ type: 'SET_SEGMENT_GROUP_LOGIC', payload: logic });
  }, []);

  return {
    state,
    actions: {
      setMode,
      setSegment,
      addGroup,
      removeGroup,
      setGroupLogic,
      addCondition,
      updateCondition,
      removeCondition,
      setPreview,
      setLoading,
      setError,
      addChatMessage,
      clearChat,
      resetSegment,
      setSegmentGroupLogic,
    },
  };
}

export type SegmentActions = ReturnType<typeof useSegmentState>['actions'];
