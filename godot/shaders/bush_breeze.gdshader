shader_type spatial;
render_mode cull_back;
uniform vec3 root_color : source_color = vec3(0.14,0.24,0.105);
uniform vec3 tip_color : source_color = vec3(0.45,0.59,0.23);
void vertex(){
    float crown=smoothstep(0.18,1.3,VERTEX.y);
    float phase=dot(MODEL_MATRIX[3].xz,vec2(0.71,1.93));
    float gust=sin(TIME*0.83+phase)+0.35*sin(TIME*1.57+phase*0.63);
    VERTEX.x+=gust*0.055*crown*crown;
    VERTEX.z+=sin(TIME*0.68+phase*1.31)*0.035*crown*crown;
    COLOR=vec4(mix(root_color,tip_color,crown),1.0);
}
void fragment(){ALBEDO=COLOR.rgb;ROUGHNESS=0.92;SPECULAR=0.16;}
