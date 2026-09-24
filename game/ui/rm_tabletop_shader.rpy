init -7 python:
    # Convex Blender parts, layered for our fixed-yaw camera's occlusion.
    renpy.register_shader("rm.check_table",variables="""
        attribute vec4 a_position;
        attribute vec3 a_normal;
        uniform mat4 u_transform;
        uniform vec3 u_table_up;
        uniform vec3 u_table_view;
        uniform vec3 u_table_projection;
        uniform vec4 u_table_shadow0;
        uniform vec4 u_table_shadow1;
        uniform vec4 u_table_shadow2;
        uniform float u_table_surface;
        uniform vec2 u_table_inner;
        uniform vec3 u_table_deck;
        uniform vec3 u_table_shell;
        uniform vec3 u_table_cap;
        uniform vec3 u_table_accent;
        uniform vec3 u_table_shade;
        varying vec3 v_table_position;
        varying vec3 v_table_normal;
    """,vertex_300="""
        v_table_position = a_position.xyz;
        v_table_normal = a_normal;
        vec3 p = a_position.xyz;
        vec4 projected = vec4(u_table_projection.x+p.x*u_table_projection.z,
            -u_table_projection.y+dot(p,u_table_up)*u_table_projection.z,0.0,1.0);
        gl_Position = u_transform * projected;
    """,fragment_functions="""
        float rm_table_shadow(vec3 p,vec4 body) {
            vec2 offset = p.xy-body.xy-vec2(0.23,0.15)*body.z;
            float radius = 0.47+max(0.0,body.z-0.45)*0.15;
            float d = length(offset)/radius;
            return (1.0-smoothstep(0.48,1.35,d))*0.40*body.w/(1.0+body.z*0.3);
        }
    """,fragment_300="""
        vec3 n = normalize(v_table_normal);
        if (dot(n,u_table_view) <= 0.0001) discard;
        vec3 p = v_table_position;
        vec3 light = normalize(vec3(-0.5,-0.7,1.0));
        float diffuse = dot(n,light);
        // Broad cel value groups, not fine screen-space noise.
        float tone = 0.56+0.20*smoothstep(0.10,0.14,diffuse)
                         +0.27*smoothstep(0.63,0.67,diffuse);
        vec3 color;
        if (u_table_surface < 0.5) {
            float edgeDistance = min(u_table_inner.x-abs(p.x),u_table_inner.y-abs(p.y));
            float occlusion = (1.0-smoothstep(0.0,0.21,edgeDistance))*0.32;
            float shadow = rm_table_shadow(p,u_table_shadow0)+rm_table_shadow(p,u_table_shadow1)+rm_table_shadow(p,u_table_shadow2);
            color = u_table_deck*tone;
            // Painted perimeter inlay; no selectable slots.
            float inlay = smoothstep(0.18,0.195,edgeDistance)*(1.0-smoothstep(0.21,0.225,edgeDistance));
            color = mix(color,u_table_cap,inlay*0.36);
            float wash = clamp((p.x+p.y+5.0)/12.0,0.0,1.0);
            color += vec3(0.025,0.035,0.027)*wash;
            color = mix(color,u_table_shade,min(0.64,shadow+occlusion));
        } else {
            float top = smoothstep(0.68,0.75,n.z);
            color = mix(u_table_shell,u_table_cap,top)*tone;
            float bevel = step(0.05,n.z)*(1.0-step(0.98,n.z));
            color += u_table_cap*bevel*max(0.0,diffuse)*0.18;
            float offset = max(abs(p.x)-u_table_inner.x,abs(p.y)-u_table_inner.y);
            float stripe = smoothstep(0.075,0.085,offset)*(1.0-smoothstep(0.115,0.125,offset))*top;
            float cornerBreak = 1.0-step(u_table_inner.x-0.13,abs(p.x))*step(u_table_inner.y-0.13,abs(p.y));
            color = mix(color,u_table_accent*tone,stripe*cornerBreak);
            float sheen = smoothstep(0.91,0.96,dot(n,normalize(light+u_table_view)))*0.055;
            color += vec3(sheen)*top;
        }
        gl_FragColor = vec4(color,1.0);
    """)
