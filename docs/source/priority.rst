=================
Priorty Functions
=================

Optimal scheduling of observations is a complex planning problem that requires a
joint analysis of all targets and the future time series of sensor positions.

Slewpy finds a good approximate solution using a separate priority function for each target.  At each decision point, 
each target's priority function returns a numerical priority value for the target, without awareness of the other 
targets or sensor positions. The scheduler then selects for observation the highest priority target that has a
visible viewing geometry.

The priority function can return a value on an arbitrary scale. However, we have found that a rational way to
assign priority is according to a target's *ideal time to its next observation*. For example, if a target's
desired cadence is :math:`T` (say :math:`T = 6~\mathrm{hr}`) and it was last observed at time
:math:`t_\mathrm{last}`, its ideal time of next observation would be :math:`t = t_\mathrm{last} + T` and 
its priority should be

.. math::

   \mathrm{priority} = -\left[ (t_\mathrm{last} + T) - t_\mathrm{cur} \right],

where :math:`t_\mathrm{cur}` is the current time. The overall minus sign means that a more imminent next ideal observation
gets a higher priority. In this case, a negative priority is the amount of slack before the ideal next observation, while a
positive priority means the target is "overdue" for an observation.