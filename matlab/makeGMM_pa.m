function makeGMM_pa(ofn, fname)
% makeGMM_pa(ofn, fname)
% calls "density_model" on fname for a number of values of "centers"
% this stores a model in fname_model.mat. This (string) is stored in 
% the file ofn
% (This is an XModeL compliant wrapper)

try
  fname=fname(1:length(fname)-4)
  centers=[10:5:35];
  iters=9;
  density_model(fname, centers, iters);
  fname=[fname '_model.mat'];
  save(ofn,'fname')
catch
  fname
end
exit

