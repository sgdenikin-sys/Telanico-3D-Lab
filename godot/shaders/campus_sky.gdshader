shader_type sky;
// Static cloud radiance is cached; no TIME or per-frame sky regeneration.
uniform vec3 sun_direction = vec3(0.666667,0.333333,-0.666667);
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise2(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
void sky(){
    if(!AT_CUBEMAP_PASS){COLOR=texture(RADIANCE,EYEDIR).rgb;}else{
    vec3 d=normalize(EYEDIR);
    float h=clamp(d.y,0.0,1.0);
    vec3 base=mix(vec3(0.76,0.84,0.88),vec3(0.30,0.57,0.82),pow(h,0.55));
    vec2 uv=d.xz/max(d.y+0.18,0.2)*2.1;
    float n=noise2(uv)*0.63+noise2(uv*2.13+7.3)*0.27+noise2(uv*4.21)*0.10;
    float cloud=smoothstep(0.51,0.72,n)*smoothstep(0.02,0.24,d.y);
    base=mix(base,vec3(0.96,0.95,0.90),cloud*0.86);
    float sun=max(dot(d,normalize(sun_direction)),0.0);
    base+=vec3(0.26,0.15,0.045)*pow(sun,16.0);
    base=mix(base,vec3(1.0,0.86,0.58),smoothstep(0.99975,0.99992,sun));
    COLOR=mix(vec3(0.26,0.38,0.43),base,smoothstep(-0.16,0.02,d.y));
    }
}
