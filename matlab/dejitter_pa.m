function dejitter_pa(ofn, fname)

% (This is an XModeL compliant wrapper)
load(fname)
ms=SampRate/1000;
rawwaves=values';
xfront=10*ms;
le=size(rawwaves, 2)-2*xfront;
s=3;
win=[-3*s 4];
size(rawwaves)
[mean2,sindex,stims,mean1,num,pct,sout]=realign2_wrapperm(rawwaves,xfront,le,win*ms,200,s*ms);
save(ofn, 'mean2', 'sindex', '-V6')
%save('temp.mat', 'mean2', 'sindex', '-V6')
quit
