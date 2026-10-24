# Tasks

For each task, write the `where` condition that selects exactly the described runs.

t01. Runs that have finished.
t02. Runs with a learning rate below 1e-3.
t03. Runs with a learning rate between 1e-4 and 1e-3, both inclusive.
t04. Runs with a warmup of 500 or 1000 steps.
t05. Runs tagged `baseline`.
t06. Runs that are not tagged `baseline`.
t07. Finished runs whose best validation accuracy is at least 0.92.
t08. Runs that failed or were killed.
t09. Runs using the adam optimizer with a learning rate of either 3e-4 or 1e-3.
t10. Runs whose name starts with `boosted`.
t11. Runs in which the training loss had at least one NaN or Inf value.
t12. Runs whose mean validation loss between steps 1000 and 2000 is below 0.5.
t13. Runs that set a weight decay at all.
t14. Runs whose proposal check failed although their verdict is `confirmed`.
t15. Runs with 12, 24 or 48 layers whose dropout is not 0.
t16. Runs with a batch size of at least 256 and a learning rate of at most 2e-3 that did not fail.
t17. Runs with seed 0 whose smoothed final training loss is below 1.5 or whose best validation accuracy is above 0.9.
t18. Runs with a mixup alpha above 0.2.
t19. Runs using the `cosine with restarts` scheduler.
t20. All runs except those that are lost and those still running with fewer than 1000 steps.
