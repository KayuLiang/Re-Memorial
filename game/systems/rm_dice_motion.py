"""Presentation-only dice motion. No character, check rules or gameplay RNG."""
import math
import random
import copy

STEP = 1.0 / 120
VIEW = (0, -.819, .574)
TABLE_LIMITS = (4.1, 1.5)


def camera(progress=1.0, selection=False):
    """Shared orthographic camera; the two screens meet at the same pixel pose."""
    t = max(0, min(1, progress))
    t = t*t*(3-2*t)
    pitch = math.radians(22+68*t)
    return dict(view=(0,-math.cos(pitch),math.sin(pitch)),
                up=(0,math.sin(pitch),math.cos(pitch)),scale=112+14*t,
                center=(968,175 if selection else 340+10*t))


def staging_pose(model):
    return landing_pose(model, 0)


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def unit(v):
    length = math.sqrt(dot(v, v))
    return tuple(x/length for x in v)


def multiply(a, b):
    w, x, y, z = a
    s, u, v, t = b
    return (w*s-x*u-y*v-z*t, w*u+x*s+y*t-z*v,
            w*v-x*t+y*s+z*u, w*t+x*v-y*u+z*s)


def axis_angle(axis, angle):
    axis = unit(axis)
    return (math.cos(angle/2),) + tuple(x*math.sin(angle/2) for x in axis)


def rotate(q, v):
    w,x,y,z = q
    a,b,c = v
    tx,ty,tz = y*c-z*b,z*a-x*c,x*b-y*a
    return (a+2*(w*tx+y*tz-z*ty),b+2*(w*ty+z*tx-x*tz),c+2*(w*tz+x*ty-y*tx))


def align(a, b):
    a, b = unit(a), unit(b)
    if dot(a, b) < -.999999:
        return axis_angle(cross(a, (1, 0, 0) if abs(a[0]) < .9 else (0, 1, 0)), math.pi)
    return unit((1+dot(a, b),) + cross(a, b))


def blend(a, b, t):
    if dot(a, b) < 0:
        b = tuple(-v for v in b)
    return unit(tuple(x+(y-x)*t for x, y in zip(a, b)))


def landing_pose(model, face_index):
    """Put a supporting face on the table, with the result facing the reader."""
    face = model['faces'][face_index]
    support = face if 'outcome_vertices' in model else min(model['faces'], key=lambda f: dot(f['normal'], face['normal']))
    q = align(support['normal'], (0, 0, -1))
    normal = rotate(q, face['normal'])
    up = rotate(q, face['up'])
    yaw = (-math.pi/2-math.atan2(normal[1], normal[0]) if math.hypot(*normal[:2]) > .01
           else math.pi/2-math.atan2(up[1], up[0]))
    return multiply(axis_angle((0, 0, 1), yaw), q)


def floor_height(body):
    return -min(rotate(body['q'], vertex)[2] for vertex in body['model']['vertices'])


def outcome(model,q):
    if 'outcome_vertices' in model:
        return max(range(4),key=lambda i:rotate(q,model['vertices'][model['outcome_vertices'][i]])[2])
    return max(range(len(model['faces'])),key=lambda i:rotate(q,model['faces'][i]['normal'])[2])


def make_world(rows, models, seed=None):
    rng = random.Random(seed)
    bodies = []
    for index, row in enumerate(rows):
        model = models[str(len(row['faces']))]
        result_face = rng.choice([i for i, value in enumerate(row['faces']) if value == row['value']])
        body = dict(model=model, faces=tuple(row['faces']), result_face=result_face,
            target=landing_pose(model, result_face),
            q=landing_pose(model, rng.randrange(len(row['faces']))),
            p=[(index-(len(rows)-1)/2)*2.5, -1.35, 0], v=[0,0,0], omega=[0,0,0],
            contacts=0, sleep=0.0, settled=False)
        body['p'][2] = floor_height(body)
        bodies.append(body)
    return dict(bodies=bodies, seed=rng.getrandbits(64), elapsed=0.0, remainder=0.0,
                phase='ready', contacts=0, throws=0)


def throw(world, dx=0, dy=-240, reduced=False):
    if world['phase'] != 'ready':
        return False
    rng = random.Random(world['seed'])
    length = math.hypot(dx, dy)
    if length < 20:
        dx, dy, length = 0, -240, 240
    power = min(1, max(.18, length/520))
    for body in world['bodies']:
        body['v'] = [dx/length*(4+power*7)+rng.uniform(-1.8,1.8),
                     -dy/length*(3+power*5)+rng.uniform(-1,1), 3.6+power*1.6+rng.uniform(0,.7)]
        body['omega'] = [rng.uniform(-13,13), rng.uniform(-13,13), rng.uniform(-9,9)]
        if reduced:
            body['q'] = body['target']
            body['p'][2] = floor_height(body)
            body['settled'] = True
    world['phase'] = 'settled' if reduced or not world['bodies'] else 'rolling'
    world['throws'] += 1
    if world['phase'] == 'rolling':
        # Predict once using presentation RNG and this exact solver. Keep the
        # unlabelled geometry simulation canonical; a constant local symmetry
        # places the chosen value on its natural resting side. No landing pose
        # correction, face relabelling, or second gameplay RNG call occurs.
        preview = copy.deepcopy(world)
        while preview['phase'] == 'rolling' and preview['elapsed'] < 10:
            step(preview)
        if preview['phase'] != 'settled':
            raise RuntimeError('Dice contact solver did not reach rest')
        for body,rest in zip(world['bodies'],preview['bodies']):
            natural = outcome(body['model'],rest['q'])
            symmetry = next(s for s in body['model']['symmetries'] if s['permutation'][body['result_face']] == natural)
            body['symmetry'] = symmetry['q']
            body['physics_q'] = body['q']
            body['release_q'] = multiply(body['q'],symmetry['q'])
            body['windup_q'] = body['q']
            body['release_p'] = list(body['p'])
        world['windup'] = 0.0
    return True


def ground_contact(body,world):
    p,v,w = body['p'],body['v'],body['omega']
    vertices = [rotate(body['q'],vertex) for vertex in body['model']['vertices']]
    bottom = min(r[2] for r in vertices)
    if p[2]+bottom > .003:
        body['sleep'] = 0.0
        return
    p[2] = max(p[2],-bottom)
    contacts = sorted((r for r in vertices if r[2]-bottom < .002),key=lambda r:(r[0],r[1],r[2]))
    # Unit mass and isotropic inertia. Multiple vertex contacts resist tipping;
    # friction acts at the contact, not by steering the orientation to a face.
    inverse_inertia = 5.0
    impact = min(v[2]+cross(w,r)[2] for r in contacts)
    if impact < -1:
        body['contacts'] += 1
        world['contacts'] += 1
    for iteration in range(6):
        for r in contacts:
            cv = [v[i]+cross(w,r)[i] for i in range(3)]
            restitution = .24 if iteration == 0 and cv[2] < -1 else 0
            j = max(0,-(1+restitution)*cv[2]/(1+inverse_inertia*(r[0]*r[0]+r[1]*r[1])))
            v[2] += j
            w[0] += r[1]*j*inverse_inertia
            w[1] -= r[0]*j*inverse_inertia
            cv = [v[i]+cross(w,r)[i] for i in range(3)]
            tangent_speed = math.hypot(cv[0],cv[1])
            if tangent_speed > 1e-8:
                tangent = (cv[0]/tangent_speed,cv[1]/tangent_speed,0)
                lever = cross(r,tangent)
                friction = min(.48*j,tangent_speed/(1+inverse_inertia*dot(lever,lever)))
                for i in range(3):
                    v[i] -= friction*tangent[i]
                    w[i] -= friction*lever[i]*inverse_inertia
    flat = min(rotate(body['q'],f['normal'])[2] for f in body['model']['faces']) < -.999
    # A flat contact dissipates spin; an edge must remain free to tip.
    for i in range(3):
        w[i] *= .97 if flat else .997
    if not flat and dot(v,v) < .06:
        # At very low speeds a discrete contact can pin an unstable edge.
        # Apply its gravitational tipping moment about the support point;
        # this depends only on geometry, never on the chosen result slot.
        pivot = [sum(r[i] for r in contacts)/len(contacts) for i in range(3)]
        torque = cross(pivot,(0,0,18))
        for i in range(3):
            w[i] += torque[i]*inverse_inertia*STEP
    quiet = dot(v,v) < .015 and dot(w,w) < .06 and flat
    body['sleep'] = body['sleep']+STEP if quiet else 0.0


def step(world):
    world['elapsed'] += STEP
    bodies = world['bodies']
    for body in bodies:
        if body['settled']:
            continue
        p, v, omega = body['p'], body['v'], body['omega']
        speed = math.sqrt(dot(omega, omega))
        if speed > .001:
            body['q'] = unit(multiply(axis_angle(omega, speed*STEP), body['q']))
        v[2] -= 18*STEP
        for i in range(3):
            p[i] += v[i]*STEP
            omega[i] *= .999
        ground_contact(body,world)
        # Table rails use the same die radius as the pairwise broad phase.
        for i, limit in enumerate(TABLE_LIMITS):
            if abs(p[i]) > limit:
                p[i] = math.copysign(limit,p[i])
                if p[i]*v[i] > 0:
                    v[i] *= -.38
                    omega[2] += v[i]*.6
                    if abs(v[i]) > .1:
                        body['sleep'] = 0.0
                    world['contacts'] += 1
    # Presentation uses spherical pair contacts; the exported convex vertices
    # still determine ground contact and drawing. Three dice do not need a SDK.
    for i, a in enumerate(bodies):
        for b in bodies[i+1:]:
            # Lateral broad-phase contacts keep this shallow tray from creating
            # false sphere-on-sphere stacks above the actual convex ground.
            if abs(b['p'][2]-a['p'][2]) > 1.25:
                continue
            delta = [b['p'][0]-a['p'][0],b['p'][1]-a['p'][1],0]
            distance = math.sqrt(dot(delta,delta))
            if distance >= 1.65:
                continue
            weight_a = 0 if a['settled'] else 1
            weight_b = 0 if b['settled'] else 1
            weight = weight_a+weight_b
            if not weight:
                continue
            normal = [d/distance for d in delta] if distance > .0001 else [1,0,0]
            correction = (1.65-distance)/weight
            for j in range(3):
                a['p'][j] -= normal[j]*correction*weight_a
                b['p'][j] += normal[j]*correction*weight_b
            closing = dot([b['v'][j]-a['v'][j] for j in range(3)],normal)
            if closing < 0:
                impulse = -closing*1.25/weight
                for j in range(3):
                    a['v'][j] -= impulse*normal[j]*weight_a
                    b['v'][j] += impulse*normal[j]*weight_b
                world['contacts'] += 1
            if correction > .01 or closing < -.1:
                for body in (a,b):
                    if not body['settled']:
                        body['sleep'] = 0.0
    for body in bodies:
        body['p'][0] = max(-TABLE_LIMITS[0],min(TABLE_LIMITS[0],body['p'][0]))
        body['p'][1] = max(-TABLE_LIMITS[1],min(TABLE_LIMITS[1],body['p'][1]))
        body['p'][2] = max(body['p'][2],floor_height(body))
        if body['sleep'] >= .18:
            body['v'] = [0,0,0]
            body['omega'] = [0,0,0]
            body['settled'] = True
    if all(body['settled'] for body in bodies):
        world['phase'] = 'settled'


def advance(world, seconds):
    if world['phase'] != 'rolling':
        return
    world['remainder'] += max(0, min(seconds, .1))
    while world['remainder'] >= STEP and world['phase'] == 'rolling':
        if world.get('windup',.16) < .16:
            world['windup'] += STEP
            t = min(1,world['windup']/.16)
            for body in world['bodies']:
                body['q'] = blend(body['windup_q'],body['release_q'],t*t*(3-2*t))
                body['p'][2] = max(body['release_p'][2],floor_height(body))+.12*math.sin(math.pi*t)
            world['remainder'] -= STEP
            continue
        for body in world['bodies']:
            body['q'] = body['physics_q']
            if world['elapsed'] == 0:
                body['p'] = list(body['release_p'])
        step(world)
        for body in world['bodies']:
            body['physics_q'] = body['q']
            body['q'] = multiply(body['q'],body['symmetry'])
        world['remainder'] -= STEP


def project(point, view_camera=None):
    x,y,z = point
    cam = view_camera or camera()
    return (cam['center'][0]+x*cam['scale'],cam['center'][1]-dot(point,cam['up'])*cam['scale'])
