# core/unity_exporter.py
import json
import os

class UnityExporter:
    @staticmethod
    def export(terrain, filepath):
        """
        지형 데이터를 Unity에서 사용할 수 있는 JSON 형식으로 내보내기
        
        Args:
            terrain (Terrain): 지형 객체
            filepath (str): 저장할 파일 경로
        """
        try:
            # 디버깅 코드 추가
            print(f"UnityExporter.export called with terrain: {terrain}, filepath: {filepath}")
            
            # 지형 데이터 가져오기 (명시적으로 인자 없이 호출)
            terrain_data = terrain.export_heightmap()
            
            # 디버깅 코드 추가
            print(f"Terrain data obtained: {terrain_data.keys() if terrain_data else 'None'}")
            
            # Unity용 데이터 구조 생성
            unity_data = {
                "version": "1.0",
                "terrain": {
                    "width": terrain_data["width"],
                    "length": terrain_data["length"],
                    "height_scale": terrain_data["height_scale"],
                    "resolution": terrain_data["resolution"],
                    "heightmap": terrain_data["heightmap"]
                },
                "objects": terrain_data["terrain_objects"]
            }
            
            # JSON 파일로 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(unity_data, f, ensure_ascii=False, indent=2)
            
            # Unity 임포터 스크립트 생성 (C#)
            unity_script = UnityExporter._generate_unity_importer()
            
            # 스크립트 파일 저장 (같은 경로에 .cs 확장자로)
            script_path = os.path.splitext(filepath)[0] + "_Importer.cs"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(unity_script)
                
            print(f"Export completed to: {filepath}")
            
        except Exception as e:
            import traceback
            print(f"Error in UnityExporter.export: {str(e)}")
            print(traceback.format_exc())
            raise e                
    @staticmethod
    def _generate_unity_importer():
        """
        Unity에서 JSON 파일을 임포트하는 C# 스크립트 생성
        
        Returns:
            str: Unity C# 스크립트 코드
        """
        return """// TerrainImporter.cs
using UnityEngine;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;

#if UNITY_EDITOR
[System.Serializable]
public class TerrainHeightmap
{
    public float[][] heightmap;
}

[System.Serializable]
public class TerrainDefinition
{
    public float width;
    public float length;
    public float height_scale;
    public float resolution;
    public float[][] heightmap;
}

[System.Serializable]
public class Vector3Data
{
    public float x;
    public float y;
    public float z;
    
    public Vector3 ToVector3()
    {
        return new Vector3(x, y, z);
    }
}

[System.Serializable]
public class TerrainObject
{
    public string type;
    public Vector3Data center;
    public Vector3Data start;
    public Vector3Data end;
    public float width;
    public float length;
}

[System.Serializable]
public class TerrainData
{
    public string version;
    public TerrainDefinition terrain;
    public List<TerrainObject> objects;
}

public class TerrainImporter : EditorWindow
{
    private string jsonFilePath = "";
    private Terrain terrain;
    
    [MenuItem("Tools/Import Terrain")]
    public static void ShowWindow()
    {
        GetWindow<TerrainImporter>("Terrain Importer");
    }
    
    private void OnGUI()
    {
        GUILayout.Label("Terrain Importer", EditorStyles.boldLabel);
        
        EditorGUILayout.BeginHorizontal();
        jsonFilePath = EditorGUILayout.TextField("JSON File:", jsonFilePath);
        if (GUILayout.Button("Browse", GUILayout.Width(80)))
        {
            string path = EditorUtility.OpenFilePanel("Select Terrain JSON", "", "json");
            if (!string.IsNullOrEmpty(path))
            {
                jsonFilePath = path;
                Repaint();
            }
        }
        EditorGUILayout.EndHorizontal();
        
        terrain = (Terrain)EditorGUILayout.ObjectField("Target Terrain:", terrain, typeof(Terrain), true);
        
        EditorGUILayout.Space();
        
        if (GUILayout.Button("Import Terrain"))
        {
            ImportTerrain();
        }
    }
    
    private void ImportTerrain()
    {
        if (string.IsNullOrEmpty(jsonFilePath))
        {
            EditorUtility.DisplayDialog("Error", "Please select a JSON file.", "OK");
            return;
        }
        
        if (terrain == null)
        {
            EditorUtility.DisplayDialog("Error", "Please assign a terrain object.", "OK");
            return;
        }
        
        try
        {
            // Read JSON file
            string jsonContent = File.ReadAllText(jsonFilePath);
            TerrainData terrainData = JsonUtility.FromJson<TerrainData>(jsonContent);
            
            if (terrainData == null || terrainData.terrain == null)
            {
                EditorUtility.DisplayDialog("Error", "Invalid JSON format.", "OK");
                return;
            }
            
            // Import heightmap
            ImportHeightmap(terrainData.terrain);
            
            // Import objects (ramps, platforms)
            if (terrainData.objects != null && terrainData.objects.Count > 0)
            {
                ImportTerrainObjects(terrainData.objects);
            }
            
            EditorUtility.DisplayDialog("Success", "Terrain imported successfully!", "OK");
        }
        catch (System.Exception e)
        {
            EditorUtility.DisplayDialog("Error", "Failed to import terrain: " + e.Message, "OK");
            Debug.LogError("Terrain import error: " + e);
        }
    }
    
    private void ImportHeightmap(TerrainDefinition terrainDef)
    {
        // Get terrain data
        UnityEngine.TerrainData terrainData = terrain.terrainData;
        
        // Set terrain size
        Vector3 size = terrainData.size;
        size.x = terrainDef.width;
        size.z = terrainDef.length;
        size.y = terrainDef.height_scale;
        terrainData.size = size;
        
        // Set resolution based on imported data
        int resolution = terrainDef.heightmap.Length;
        
        // Ensure resolution is valid (power of 2 plus 1)
        int validResolution = Mathf.ClosestPowerOfTwo(resolution - 1) + 1;
        if (validResolution != resolution)
        {
            Debug.LogWarning("Adjusting heightmap resolution from " + resolution + " to " + validResolution);
            resolution = validResolution;
        }
        
        terrainData.heightmapResolution = resolution;
        
        // Prepare heights array
        float[,] heights = new float[resolution, resolution];
        
        // Fill heights array from JSON data
        for (int x = 0; x < terrainDef.heightmap.Length; x++)
        {
            for (int z = 0; z < terrainDef.heightmap[x].Length; z++)
            {
                if (x < resolution && z < resolution)
                {
                    // Convert height to normalized value (0-1)
                    heights[z, x] = terrainDef.heightmap[x][z] / terrainDef.height_scale;
                }
            }
        }
        
        // Apply heights to terrain
        terrainData.SetHeights(0, 0, heights);
    }
    
    private void ImportTerrainObjects(List<TerrainObject> objects)
    {
        // Create a parent object for all terrain objects
        GameObject objectsParent = new GameObject("TerrainObjects");
        objectsParent.transform.position = terrain.transform.position;
        
        foreach (TerrainObject obj in objects)
        {
            if (obj.type == "ramp")
            {
                CreateRamp(obj, objectsParent.transform);
            }
            else if (obj.type == "platform")
            {
                CreatePlatform(obj, objectsParent.transform);
            }
        }
    }
    
    private void CreateRamp(TerrainObject obj, Transform parent)
    {
        // Get start and end positions
        Vector3 start = obj.start.ToVector3();
        Vector3 end = obj.end.ToVector3();
        
        // Calculate direction and length
        Vector3 direction = end - start;
        float length = direction.magnitude;
        direction.Normalize();
        
        // Create ramp object
        GameObject ramp = GameObject.CreatePrimitive(PrimitiveType.Cube);
        ramp.name = "Ramp";
        ramp.transform.parent = parent;
        
        // Position at midpoint
        ramp.transform.position = (start + end) * 0.5f;
        ramp.transform.position = new Vector3(
            ramp.transform.position.x,
            (start.y + end.y) * 0.5f,
            ramp.transform.position.z
        );
        
        // Scale to match dimensions
        ramp.transform.localScale = new Vector3(obj.width, 0.1f, length);
        
        // Rotate to match direction
        ramp.transform.forward = direction;
        
        // Adjust Y rotation to match slope
        float slopeAngle = Mathf.Atan2(end.y - start.y, length) * Mathf.Rad2Deg;
        ramp.transform.Rotate(slopeAngle, 0, 0);
    }
    
    private void CreatePlatform(TerrainObject obj, Transform parent)
    {
        // Create platform object
        GameObject platform = GameObject.CreatePrimitive(PrimitiveType.Cube);
        platform.name = "Platform";
        platform.transform.parent = parent;
        
        // Set position
        platform.transform.position = obj.center.ToVector3();
        
        // Set scale
        platform.transform.localScale = new Vector3(obj.width, 0.1f, obj.length);
    }
}
#endif
"""