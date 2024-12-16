#version 330 core
out vec4 FragColor;

struct Material {
    sampler2D diffuseSampler;
    sampler2D specularSampler;
    sampler2D normalSampler;
    float shininess;
}; 

struct Light {
    vec3 dir;
    vec3 color; // this is I_d (I_s = I_d, I_a = 0.3 * I_d)
};

uniform vec3 viewPos;
uniform Material material;
uniform Light light;
uniform sampler2D depthMapSampler;
// For csm
uniform sampler2D depthMapSamplers[3];
// uniform mat4 lightSpaceMatrices[3];
uniform float cascadeDistances[3];

in vec2 TexCoord;
in vec3 FragPos;
in vec3 Normal; 
in vec3 Tangent;
in vec3 Bitangent;
in vec4 FragPosLightSpace;
in vec4 FragPosLightSpaces[3];
in float EyeSpaceDepth;
uniform bool usePCF;
uniform bool useCSM;
uniform float useNormalMap;
uniform float useSpecularMap;
uniform float useShadow;
uniform float useLighting;


vec2 poissonDisk[16] = vec2[](
    vec2(-0.94201624, -0.39906216), vec2(0.94558609, -0.76890725),
    vec2(-0.094184101, -0.92938870), vec2(0.34495938, 0.29387760),
    vec2(-0.91588581, 0.45771432), vec2(-0.81544232, -0.87912464),
    vec2(-0.38277543, 0.27676845), vec2(0.97484398, 0.75648379),
    vec2(0.44323325, -0.97511554), vec2(0.53742981, -0.47373420),
    vec2(-0.26496911, -0.41893023), vec2(0.79197514, 0.19090188),
    vec2(-0.24188840, 0.99706507), vec2(-0.81409955, 0.91437590),
    vec2(0.19984126, 0.78641367), vec2(0.14383161, -0.14100790)
);

float random(vec3 seed, int i) {
    vec4 seed4 = vec4(seed, float(i));
    float dot_product = dot(seed4, vec4(42.32, 103.4123, 4.23123, 12312.0029));
    return fract(sin(dot_product) * 231.5453);
}

float ShadowCalculation_PCF(sampler2D depthMap, vec4 fragPosLightSpace) {
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;
    projCoords = projCoords * 0.5 + 0.5;

    if (projCoords.z > 1.0) return 0.0;

    float shadow = 0.0;
    float samples = 4.0;
    float offset = 1.0 / 2048.0;

    for (int i = 0; i < 4; i++) {
        int index = int(16.0 * random(gl_FragCoord.xyy, i)) % 16;
        vec2 samplePos = projCoords.xy + poissonDisk[index] * offset;
        float sampleDepth = texture(depthMap, samplePos).r;

        if (projCoords.z - 0.003 > sampleDepth) {
            shadow += 1.0;
        }

    }
    shadow /= samples;

    return shadow;
}

float ShadowCalculation_base(sampler2D depthMap, vec4 fragPosLightSpace) {
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;
    projCoords = projCoords * 0.5 + 0.5; // Map to [0, 1] range

    if (projCoords.z > 1.0)
        return 0.0;
    float closestDepth = texture(depthMap, projCoords.xy).r;
    float currentDepth = projCoords.z;
    float bias = max(0.003 * (1.0 - dot(Normal, light.dir)), 0.001);

    float shadow = currentDepth - bias > closestDepth ? 1.0 : 0.0;

    return shadow;
}

// float ShadowCalculation(vec4 fragPosLightSpace) {
//     if (usePCF) {
//         return ShadowCalculation_PCF(fragPosLightSpace);
//     } else {
//         return ShadowCalculation_base(fragPosLightSpace);
//     }
// }
float ShadowCalculation(vec4 fragPosLightSpace, int cascadeIndex) {
    if (usePCF) {
        if (cascadeIndex == -1) {
            return ShadowCalculation_PCF(depthMapSampler, fragPosLightSpace);
        } else if (cascadeIndex == 0) {
            return ShadowCalculation_PCF(depthMapSamplers[0], fragPosLightSpace);
        } else if (cascadeIndex == 1) {
            return ShadowCalculation_PCF(depthMapSamplers[1], fragPosLightSpace);
        } else if (cascadeIndex == 2) {
            return ShadowCalculation_PCF(depthMapSamplers[2], fragPosLightSpace);
        } 
    } else {
        if (cascadeIndex == -1) {
            return ShadowCalculation_base(depthMapSampler, fragPosLightSpace);
        } else if (cascadeIndex == 0) {
            return ShadowCalculation_base(depthMapSamplers[0], fragPosLightSpace);
        } else if (cascadeIndex == 1) {
            return ShadowCalculation_base(depthMapSamplers[1], fragPosLightSpace);
        } else if (cascadeIndex == 2) {
            return ShadowCalculation_base(depthMapSamplers[2], fragPosLightSpace);
        } 
    }
    return 0.0; // 기본 반환 값 (예외 상황)
}

float CascadedShadowCalculation(vec4 fragPosLightSpaces[3], float EyeSpaceDepth) {
    float currentDepth = EyeSpaceDepth;

    if (currentDepth < cascadeDistances[0]) {
        return ShadowCalculation(fragPosLightSpaces[0], 0);
    } else if (currentDepth < cascadeDistances[1]) {
        return ShadowCalculation(fragPosLightSpaces[1], 1);
    } else if (currentDepth < cascadeDistances[2]) {
        return ShadowCalculation(fragPosLightSpaces[2], 2);
    } else {
        return 0.0;  // If depth is beyond the cascades, no shadow
    }
}

void main()
{

    // // on-off by key 3 (useLighting). 
    // // if useLighting is 0, return diffuse value without considering any lighting.(DO NOT CHANGE)
    vec3 kd = texture(material.diffuseSampler, TexCoord).rgb;  // Diffuse reflectance coefficient

    // vec3 color = texture(material.diffuseSampler, TexCoord).rgb;
    if (useLighting < 0.5f) {
        FragColor = vec4(kd, 1.0); 
        return;
    }

    vec3 ambient = 0.3 * kd * light.color; // Ambient lighting component (assume ka = kd and Ia = 0.3 * Id)

    // // on-off by key 2 (useShadow).
    // // calculate shadow
    // // if useShadow is 0, do not consider shadow.
    // // if useShadow is 1, consider shadow.

    // float shadow = useShadow > 0.5 ? ShadowCalculation(FragPosLightSpace) : 0.0;
    float shadow = 0.0;
    if (useShadow > 0.5) {
        if (useCSM) {
            shadow = CascadedShadowCalculation(FragPosLightSpaces, EyeSpaceDepth);
        } else {
            shadow = ShadowCalculation(FragPosLightSpace, -1);
        }
    }

    // // on-off by key 1 (useNormalMap).
    // // if model does not have a normal map, this should be always 0.
    // // if useNormalMap is 0, we use a geometric normal as a surface normal.
    // // if useNormalMap is 1, we use a geometric normal altered by normal map as a surface normal.
    vec3 norm = normalize(Normal); // Surface normal (provided in the shader)
    if (useNormalMap > 0.5) {
        vec3 normalColor = texture(material.normalSampler, TexCoord).rgb;
        normalColor = normalColor * 2.0 - 1.0;  // [0, 1] -> [-1, 1] 범위 조정
        normalColor = normalize(normalColor);
        mat3 TBN = mat3(Tangent, Bitangent, Normal);
        norm = normalize(TBN * normalColor);     // Tangent Space 변환
    }

    vec3 L = normalize(-light.dir);                   // Light direction (reverse of light.dir)
    vec3 V = normalize(viewPos - FragPos);            // View direction (camera to fragment)
    vec3 R = reflect(-L, norm);                       // Reflected light direction around the normal

    // Diffuse component (Lambertian reflectance)
    float diff = max(dot(norm, L), 0.0);              // cos(theta) for diffuse light
    vec3 diffuse = kd * light.color * diff;           // Diffuse light intensity

    // // if model does not have a specular map, this should be always 0.
    // // if useSpecularMap is 0, ignore specular lighting.
    // // if useSpecularMap is 1, calculate specular lighting.
    float spec = 0.0;
    vec3 specular = vec3(0.0);
    if(useSpecularMap > 0.5f && diff > 0.0)
    {
        float ks = texture(material.specularSampler, TexCoord).r;  // Specular reflectance coefficient (red channel only)
        spec = pow(max(dot(R, V), 0.0), material.shininess);  // Phong specular term
        specular = ks * light.color * spec;          // Specular light intensity
    }
    vec3 I = (ambient + (1.0 - shadow) * (diffuse + specular));
    FragColor = vec4(I, 1.0);
}

