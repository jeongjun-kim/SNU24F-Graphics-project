#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoord;
layout (location = 2) in vec3 aNormal;
layout (location = 3) in vec3 aTangent;

out vec2 TexCoord;
out vec3 FragPos;       // 프래그먼트 위치
out vec3 Normal;        // 표면 노멀 벡터
out vec3 Tangent;
out vec3 Bitangent;
out vec4 FragPosLightSpace;
out vec4 FragPosLightSpaces[3];
out float EyeSpaceDepth;
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 lightSpaceMatrix;
uniform mat4 lightSpaceMatrices[3];

uniform float useNormalMap;
uniform float useShadow;

void main()
{

	// on-off by key 1 (useNormalMap).
    // if model does not have a normal map, this should be always 0.
    // if useNormalMap is 0, we use a geometric normal as a surface normal.
    // if useNormalMap is 1, we use a geometric normal altered by normal map as a surface normal.
	
	Normal = normalize(mat3(transpose(inverse(model))) * aNormal);
	TexCoord = aTexCoord;
	FragPos = vec3(model * vec4(aPos, 1.0));

	gl_Position = projection * view * model * vec4(aPos, 1.0f);
	FragPosLightSpace = lightSpaceMatrix * model * vec4(aPos, 1.0);
	FragPosLightSpaces[0] = lightSpaceMatrices[0] * model * vec4(aPos, 1.0);
	FragPosLightSpaces[1] = lightSpaceMatrices[1] * model * vec4(aPos, 1.0);
	FragPosLightSpaces[2] = lightSpaceMatrices[2] * model * vec4(aPos, 1.0);

	Tangent = normalize(mat3(model) * aTangent);
	Bitangent = normalize(cross(Normal, Tangent));
	vec4 posInViewSpace = view * model * vec4(aPos, 1.0);
	EyeSpaceDepth = abs((view * model * vec4(aPos, 1.0)).z);

}
