import {loadState,saveState} from './runtime.uc';
let s=loadState();if(s.schema==1)saveState(s,true);
