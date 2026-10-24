shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never,fog_disabled,shadows_disabled;
varying vec2 ground;
uniform sampler2D mist_noise : repeat_enable,filter_linear;
void vertex(){ground=(MODEL_MATRIX*vec4(VERTEX,1.0)).xz;}
void fragment(){
    vec2 p=ground*0.006+vec2(TIME*0.00045,TIME*0.00022);
    float mist=smoothstep(0.40,0.72,texture(mist_noise,p).r*0.7+texture(mist_noise,p*2.1).r*0.3);
    float channel=(1.0-smoothstep(8.0,28.0,abs(ground.x)))*(1.0-smoothstep(28.0,65.0,abs(ground.y)));
    float edge=1.0-smoothstep(0.78,1.0,max(abs(UV.x*2.0-1.0),abs(UV.y*2.0-1.0)));
    ALBEDO=vec3(0.65,0.81,0.83);
    ALPHA=mist*(0.025+channel*0.085)*edge;
}
