#define GLM_ENABLE_EXPERIMENTAL
#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <glm/glm.hpp>
#include <vector>
#include <iostream>
#include <algorithm>
#include <unordered_map>
#include <functional>

namespace std {
template <>
struct hash<std::pair<int, int>> {
    size_t operator()(const std::pair<int, int>& p) const {
        return hash<int>()(p.first) ^ (hash<int>()(p.second) << 1);
    }
};
} 

static void checkGLError(const char* msg) {
    GLenum err;
    while ((err = glGetError()) != GL_NO_ERROR) {
        std::cerr << "[OpenGL Error] (" << std::hex << err << std::dec << "): " << msg << std::endl;
    }
}

extern "C" {
    bool init_glad();
    void process_vertices(float* vertices, int num_vertices, int* edges, int num_edges, float threshold);
}

extern "C" {
    bool init_glad() {
        std::cerr << "[DEBUG] Initializing GLAD..." << std::endl;
        if (!gladLoadGL()) {
            std::cerr << "[ERROR] Failed to initialize GLAD." << std::endl;
            return false;
        }
        std::cerr << "[DEBUG] GLAD initialized successfully." << std::endl;
        return true;
    }

    void process_vertices(float* vertices, int num_vertices, int* edges, int num_edges, float threshold) {
        std::cerr << "[DEBUG] Starting mesh cleanup candidate report." << std::endl;

        if (!vertices || !edges) {
            std::cerr << "[ERROR] Invalid input: vertices or edges pointer is null." << std::endl;
            return;
        }

        // 1. remove double
        std::vector<glm::vec3> vertex_data(num_vertices);
        for (int i = 0; i < num_vertices; ++i) {
            vertex_data[i] = glm::vec3(vertices[i * 3], vertices[i * 3 + 1], vertices[i * 3 + 2]);
        }

        std::sort(vertex_data.begin(), vertex_data.end(), [](const glm::vec3& a, const glm::vec3& b) {
            if (a.x == b.x) {
                if (a.y == b.y) return a.z < b.z;
                return a.y < b.y;
            }
            return a.x < b.x;
        });

        int duplicate_count = 0;
        for (size_t i = 0; i < vertex_data.size() - 1; ++i) {
            if (glm::distance(vertex_data[i], vertex_data[i + 1]) < threshold) {
                duplicate_count++;
            }
        }
        float duplicate_ratio = (float)duplicate_count / num_vertices * 100.0f;
        std::cerr << "[REPORT] Duplicate vertices: " << duplicate_count
                  << " / " << num_vertices
                  << " (" << duplicate_ratio << "%)" << std::endl;

        // 2. loose vertex count
        int loose_count = 0;
        std::vector<int> vertex_connection_count(num_vertices, 0);
        for (int i = 0; i < num_edges * 2; i += 2) {
            int v1 = edges[i];
            int v2 = edges[i + 1];
            vertex_connection_count[v1]++;
            vertex_connection_count[v2]++;
        }

        for (int i = 0; i < num_vertices; ++i) {
            if (vertex_connection_count[i] == 0) {
                loose_count++;
            }
        }
        float loose_ratio = (float)loose_count / num_vertices * 100.0f;
        std::cerr << "[REPORT] Loose elements: " << loose_count
                  << " / " << num_vertices
                  << " (" << loose_ratio << "%)" << std::endl;

    
        // interior face
        int interior_faces = 0;
        std::unordered_map<int, int> edge_use_map; // Edge (v1, v2) -> use count

        for (int i = 0; i < num_edges * 2; i += 2) {
            int v1 = edges[i];
            int v2 = edges[i + 1];
            if (v1 > v2) std::swap(v1, v2); 
            edge_use_map[v1 * num_vertices + v2]++;
        }

        for (const auto& pair : edge_use_map) {
            if (pair.second > 1) {
                interior_faces++;
            }
        }

        float interior_ratio = (float)interior_faces / num_vertices * 100.0f;
        std::cerr << "[REPORT] Interior faces: " << interior_faces
                << " / " << num_vertices
                << " (" << interior_ratio << "%)" << std::endl;

        // degenerated face
        int degenerate_faces = 0;
        for (int i = 0; i < num_edges; i += 3) {
            glm::vec3 v0 = vertex_data[edges[i]];
            glm::vec3 v1 = vertex_data[edges[i + 1]];
            glm::vec3 v2 = vertex_data[edges[i + 2]];
            float area = glm::length(glm::cross(v1 - v0, v2 - v0)) * 0.5f;
            if (area < 1e-6) {
                degenerate_faces++;
            }
        }

        float degenerate_ratio = (float)degenerate_faces / num_edges * 100.0f;
        std::cerr << "[REPORT] Degenerate faces: " << degenerate_faces
                << " / " << num_edges
                << " (" << degenerate_ratio << "%)" << std::endl;


        std::cerr << "[DEBUG] Mesh cleanup report completed." << std::endl;
    }
}
