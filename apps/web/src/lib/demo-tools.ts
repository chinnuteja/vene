'use client';
import {useEffect,useState} from 'react';
export function useDemoTools(){const [enabled,setEnabled]=useState(false);useEffect(()=>{setEnabled(sessionStorage.getItem('vene-demo-tools')==='true');},[]);return enabled;}
