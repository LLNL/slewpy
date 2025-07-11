# priority function that will linearly increase the
# priority after the most recent observation relative to desired
# average observation period
def target_priority2(target, sensor, **kwargs):
    ctime = sensor.env.t0.gps + sensor.env.now
    if len(target.obs_times) > 0:
        last_time = target.obs_times[-1]
    else:
        return sensor.env.t0.gps

    avg_period = target.obs_period / target.obs_per_period
    priority = (ctime - last_time) / avg_period

    return priority

def target_priority3(target, sensor, **kwargs):
    '''
    The average rate at which observations of this target should be made is 
        r = (number of observerations of the target that still need to be made) / (time remaining in the window for this target)
    
    For events that happen at rate r, the time until the next event is an exponential random variable.
    
    So sample this exponential "time until the next observation" for each target
     and the target with the lowest of these times should get the highest priority.
    '''
    num_obs_total = round(target.obs_per_period * (target.tfinal - target.tstart) / target.obs_period)
    num_obs_left = num_obs_total - len(target.obs_times)
    time_left = target.tfinal - sensor.env.now

    # Don't observe if we got required number of observations
    if num_obs_left <= 0:
        return -1e300

    target_rate = num_obs_left / time_left
    if sensor.rng:
        random = sensor.rng.uniform()
    else:
        random = np.random.rand()
    minus_time_til_next = np.log(random) / target_rate
    return minus_time_til_next

def target_priority4(target, sensor, **kwargs):
    '''
    Try to get regularly spaced observations.
    Time to the next observation should be (time of most recent obs) + (ideal interval between obs) - (current time)
    Target with the lowest time til next observation is highest priority.
    '''
    type = target.type

    obs_so_far = len(target.obs_times)

    now = sensor.env.now
    
    # first observation should be as soon after tstart as possible
    if obs_so_far == 0:
        time_til_next = target.tstart - now
        return -time_til_next

    last_obs = target.obs_times[-1] - sensor.env.t0.gps

    if type == 'AGN_low':
        interval = 3.*3600 # 8x per day
    
    elif type == 'AGN_med':
        interval = 12.*3600 # 2x per day
    
    elif type == 'AGN_high':
        interval = 2.*86400 # every other day
    
    elif type == 'SNe':
        interval = 2.5*86400 # every 2.5 days
   
    elif type == 'SNe_CC':
        #20 times in 3 days, then 10 times over rest of the 2 weeks
        interval = 3*86400/20 if (now - target.tstart < 3*86400) else 11*86400/10

    elif type == 'SNe_SED':
        # 2 observations as soon as possible, but don't take more than 2 obs
        interval = 0.0 if obs_so_far < 2 else 1e300

    elif type == 'TOO':
        #every day until you get 3 observations, then 2 more times over rest of the two weeks
        interval = 86400.0 if (obs_so_far < 3) else 12*86400/2
    
    else:
        raise Exception(f"target is unknown type: {target.type=}")

    time_til_next = last_obs + interval - now
    
    return -time_til_next


def target_priority5(target, sensor, **kwargs):
    '''
    Try to get regularly spaced observations.
    Adapts time-til-next-observation to try to achieve a given total number of observations.
    Time to the next observation is (time of most recent obs) + (ideal interval between obs) - (current time)
    Target with the lowest time til next observation is highest priority.

    priority = -(time til next obs)
    so if priority is negative it means target was observed ahead of ideal time,
     positive means it was observed after ideal time.
    '''
    type = target.type

    obs_so_far = len(target.obs_times)

    now = sensor.env.now
    
    # first observation should be as soon after tstart as possible
    if obs_so_far == 0:
        time_til_next = target.tstart - now
        return -time_til_next

    last_obs = target.obs_times[-1] - sensor.env.t0.gps

    if type == 'AGN_low':
        base_interval = 3.*3600 # 8x per day
        tstop = target.tstart + 90*86400. # 90 day duration
        adaptive_interval = (tstop - last_obs)/(720 - obs_so_far) # try to get 720 total obs
        interval = min(base_interval, adaptive_interval)
    
    elif type == 'AGN_med':
        base_interval = 12.*3600 # 2x per day
        tstop = target.tstart + 180*86400. # 180 day duration
        adaptive_interval = (tstop - last_obs)/(360 - obs_so_far) #try to get 360 total obs
        interval = min(base_interval, adaptive_interval)
    
    elif type == 'AGN_high':
        base_interval = 2.*86400 # every other day
        tstop = target.tstart + 730*86400. #730 day duration
        adaptive_interval = (tstop - last_obs)/(180 - obs_so_far) #try to get 180 total obs
        interval = min(base_interval, adaptive_interval)
    
    elif type == 'SNe':
        base_interval = 2.5*86400 # every 2.5 days
        tstop = target.tstart + 60*86400. # 60 day duration
        adaptive_interval = (tstop - last_obs)/(24 - obs_so_far) #try to get 24 total obs
        interval = min(base_interval, adaptive_interval)
   
    elif type == 'SNe_CC':
        #20 times in 3 days, then 10 times over rest of the 2 weeks
        phase1stop = target.tstart + 3*86400.
        if now < phase1stop:
            base_interval = 3*86400/20
            adaptive_interval = (phase1stop - last_obs)/(20 - obs_so_far)
            interval = min(base_interval, adaptive_interval)
        else:
            base_interval = 11*86400/10
            tstop = target.tstart + 14*86400. # 14 day duration
            adaptive_interval = (tstop - last_obs)/(30 - obs_so_far)
            interval = min(base_interval, adaptive_interval)

    elif type == 'SNe_SED':
        # 2 observations as soon as possible, but don't take more than 2 obs
        interval = 0.0 if obs_so_far < 2 else 1e300

    elif type == 'TOO':
        # 3 obs in first 3 days, then 2 more within the rest of the two weeks
        phase1stop = target.tstart + 3*86400.
        if obs_so_far < 3:
            base_interval = 86400.
            adaptive_interval = (phase1stop - last_obs)/(3 - obs_so_far)
            interval = min(base_interval, adaptive_interval)
        else:
            base_interval = 11*86400/2
            tstop = target.tstart + 14*86400. # 14 day duration
            adaptive_interval = (tstop - last_obs)/(5 - obs_so_far)
            interval = min(base_interval, adaptive_interval)
    
    else:
        raise Exception(f"target is unknown type: {target.type=}")

    time_til_next = last_obs + interval - now
    
    return -time_til_next



