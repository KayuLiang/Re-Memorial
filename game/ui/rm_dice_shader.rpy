init -7 python:
    def rm_dice_gl_vec(vector):
        return "vec3("+",".join("%.8f" % v for v in vector)+")"

    # Convex ray/plane intersection uses only public Model/shader APIs. The
    # constants come from our existing Blender meshes; numbers stay live text.
    for _sides, _model in RM_REALTIME_MODELS.items():
        _planes = []
        _edges = []
        for _i,_face in enumerate(_model['faces']):
            _n = rm_dice_gl_vec(_face['normal'])
            _d = rm_dice_motion.dot(_face['normal'],_face['center'])
            _planes.append("""
                {
                    vec3 planeN = %s;
                    float denom = dot(planeN, rd);
                    float gap = %.8f - dot(planeN, ro);
                    if (abs(denom) < 0.00001) {
                        if (gap < 0.0) discard;
                    } else {
                        float t = gap / denom;
                        if (denom < 0.0 && t > nearT) {
                            nearT = t; faceId = %.1f; N = planeN;
                            C = %s; R = %s; U = %s; span = %.8f;
                        }
                        if (denom > 0.0) farT = min(farT,t);
                    }
                }
            """ % (_n,_d,float(_i),rm_dice_gl_vec(_face['center']),rm_dice_gl_vec(_face['right']),rm_dice_gl_vec(_face['up']),_face['span']))
            _edges.append("if (faceId != %.1f) edge = min(edge, %.8f-dot(%s,hit));" % (float(_i),_d,_n))
        _glyphs = []
        for _i,_face in enumerate(_model['faces']):
            _glyphs.append("if (faceId == %.1f) {" % _i)
            for _label in _face.get('labels',[dict(_face,slot=_i)]):
                _glyphs.append("""{
                    vec3 local = hit-%s;
                    vec2 glyph = vec2(dot(local,%s),-dot(local,%s))/%.8f+0.5;
                    if (glyph.x>0.02 && glyph.x<0.98 && glyph.y>0.02 && glyph.y<0.98)
                        gold = max(gold,texture2D(tex0,vec2((%.1f+glyph.x)/%s.0,glyph.y)).a);
                }""" % (rm_dice_gl_vec(_label['center']),rm_dice_gl_vec(_label['right']),
                    rm_dice_gl_vec(_label['up']),_label['span'],float(_label['slot']),_sides))
            _glyphs.append("}")
        renpy.register_shader("rm.live_die_"+_sides,variables="""
            attribute vec2 a_tex_coord;
            varying vec2 v_tex_coord;
            uniform sampler2D tex0;
            uniform vec4 u_dice_q;
            uniform vec3 u_dice_view;
            uniform vec3 u_dice_up;
            uniform float u_dice_scale;
        """,vertex_300="v_tex_coord = a_tex_coord;",fragment_functions="""
            vec3 rm_qrot(vec4 q, vec3 v) {
                return v + 2.0*cross(q.yzw,cross(q.yzw,v)+q.x*v);
            }
        """,fragment_300="""
            vec3 view = u_dice_view;
            vec3 up = u_dice_up;
            vec3 rayOrigin = vec3((v_tex_coord.x-0.5)*240.0/u_dice_scale,0.0,0.0)
                - up*(v_tex_coord.y-0.5)*240.0/u_dice_scale + view*3.0;
            vec4 inverseQ = vec4(u_dice_q.x,-u_dice_q.yzw);
            vec3 ro = rm_qrot(inverseQ,rayOrigin);
            vec3 rd = rm_qrot(inverseQ,-view);
            float nearT = -1000.0;
            float farT = 1000.0;
            float faceId = -1.0;
            vec3 N = vec3(0.0);
            vec3 C = vec3(0.0);
            vec3 R = vec3(0.0);
            vec3 U = vec3(0.0);
            float span = 1.0;
        """+"\n".join(_planes)+"""
            if (nearT > farT || faceId < 0.0) discard;
            vec3 hit = ro+rd*nearT;
            vec3 worldN = normalize(rm_qrot(u_dice_q,N));
            vec3 light = normalize(vec3(-0.5,-0.7,1.0));
            float diffuse = max(0.0,dot(worldN,light));
            float grain = fract(sin(dot(floor(hit*180.0),vec3(12.9898,78.233,31.42)))*43758.5453);
            float vein = pow(abs(sin(hit.x*13.0+sin(hit.y*17.0)+hit.z*8.0)),22.0);
            float gloss = pow(max(0.0,dot(reflect(-light,worldN),view)),24.0);
            float fill = max(dot(worldN,normalize(vec3(0.8,0.4,0.6))),0.0);
            float broadSpec = pow(max(dot(worldN,normalize(light+view)),0.0),10.0);
            vec3 stone = vec3(0.105,0.14,0.16)*(0.8+diffuse*1.3)
                + vec3(0.045,0.065,0.08)*fill
                + vec3(grain*0.008+vein*0.012+gloss*0.16+broadSpec*0.10);
            float edge = 1.0;
        """+"\n".join(_edges)+"""
            stone += vec3(0.15,0.17,0.18)*(1.0-smoothstep(0.0,0.012,edge))*(0.3+diffuse);
            float gold = 0.0;
        """+"\n".join(_glyphs)+"""
            gl_FragColor = vec4(mix(stone,vec3(0.91,0.73,0.38)*(0.76+diffuse*0.30),gold),1.0);
        """)
