'use client';
import {createContext,useContext} from 'react';
import type {components} from '../../../../packages/contracts/schema';
export type ServiceViews={
  room:components['schemas']['RoomView'];
  execution:components['schemas']['ExecutionView'];
  circle:components['schemas']['CircleView'];
  feasibility:components['schemas']['FeasibilityView'];
};
export const VisitUpdates=createContext<ServiceViews|null>(null);
export const useVisitUpdates=()=>useContext(VisitUpdates);
