using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.UIElements;
using UnityEditor.UIElements;
using System.Collections.Generic;
using UnityEngine.Networking;
using System.Collections;
using System.Threading;

public class MenuTest : EditorWindow
{

    static string prompt_buffer;
    
    [MenuItem("Gen/Load...")]
    static void LoadDialogue()
    {
        string path = EditorUtility.OpenFilePanel(
            "Select a scene to load",   // window title
            "Assets/Scenes",
            "unity");                    // extension filter (e.g. "txt", "png", "json"; empty = all files)

        Load(path);
    }
    
    static void Load(string path)
    {
        
        /* // Keep this if it works while the game is running
        if (!string.IsNullOrEmpty(path))
        {
            Debug.Log("Opening scene:");
            SceneManager.LoadScene(path);
        }
        */
        if (!string.IsNullOrEmpty(path))
        {
            Debug.Log("Opening scene:");
            EditorSceneManager.OpenScene(path);
        }
        else
        {
            Debug.Log("No scene selected.");
        }
    }

    [MenuItem("Gen/Prompt")]
    static void PromptDialogue()
    {
        OpenPromptDialogue();
    }
    
    [MenuItem("Gen/Prompt and Load %g")]
    static void PromptAndLoad()
    {
        OpenPromptDialogue(); // Sets prompt_buffer
        var flaskObj = new GameObject("FlaskInterface");
        var flask = flaskObj.AddComponent<FlaskInterface>();
        flask.SendPromptToFlask(prompt_buffer);
        Debug.Log("Prompt `" + prompt_buffer + "` sent.");
        flask.StartWaitOnFlask(); //Default arg permitted in ToFlask?
        Object.DestroyImmediate(flask.gameObject);
        Load("last.unity");
    }
    
    static void OpenPromptDialogue()
    {
        TextInputDialog.Show("Enter text:", input =>
        {
            Debug.Log("User entered: " + input);
            prompt_buffer = input;
            var flaskObj = new GameObject("FlaskInterface");
            var flask = flaskObj.AddComponent<FlaskInterface>();
            flask.SendPromptToFlask(prompt_buffer);
            Debug.Log("Prompt `" + prompt_buffer + "` sent.");
            Object.DestroyImmediate(flask.gameObject);
        });
        
    }
    
    [MenuItem("Gen/Do Something")]
    static void DoSomething()
    {
        Debug.Log("Sends Scene to VR or something...");
    }
}

public class FlaskInterface : MonoBehaviour
    {
        public void SendPromptToFlask(string prompt)
        {
            StartCoroutine(this.PromptToFlask(prompt));
        }
        
        public void StartWaitOnFlask()
        {
            StartCoroutine(this.WaitOnFlask());
        }
        
        
        IEnumerator PromptToFlask(string prompt)
        {
            WWWForm form = new WWWForm();
            form.AddField("prompt", prompt);

            using UnityWebRequest www = UnityWebRequest.Post("http://localhost:5000/prompt", form);
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError(www.error);
            }
            else
            {
                string response = www.downloadHandler.text;
                if (response == "prompting")
                {
                    Debug.Log("System is: " + response);
                }
                else
                {
                    Debug.Log("System failed to prompt.");
                    Debug.Log(response);
                }
            }
        }
        
        IEnumerator WaitOnFlask()
        {
            using UnityWebRequest www = UnityWebRequest.Get("http://localhost:5000/wait");
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError(www.error);
            }
            else
            {
                string response = www.downloadHandler.text;

                if (response == "last_ready") // The last prompted world (second kind of request)
                {
                    Debug.Log("File is immediately ready.");
                }
                else
                    if (response == "last_not_ready")
                    {
                        // Call server until prompt is done
                        do
                        {
                            Thread.Sleep(100);
                            using UnityWebRequest wwwN = UnityWebRequest.Get("http://localhost:5000/wait");
                            yield return wwwN.SendWebRequest();

                            if (wwwN.result != UnityWebRequest.Result.Success)
                            {
                                Debug.LogError(wwwN.error);
                            }
                            else {
                                response = wwwN.downloadHandler.text;
                            }
                        } while (response == "last_not_ready");
                        Debug.Log("File is finally ready.");
                    }
                        
            }
        }
        
        
}

// Tiny reusable EditorWindow for text input
public class TextInputDialog : EditorWindow
{
    string input = "";
    System.Action<string> onSubmit;
    string prompt = "Input:";

    public static void Show(string prompt, System.Action<string> onSubmit)
    {
        var window = ScriptableObject.CreateInstance<TextInputDialog>();
        window.prompt = prompt;
        window.onSubmit = onSubmit;
        window.titleContent = new GUIContent(prompt);
        window.position = new Rect(Screen.width / 2, Screen.height / 2, 300, 100);
        window.ShowUtility();
    }

    void OnGUI()
    {
        GUILayout.Label(prompt, EditorStyles.boldLabel);
        input = EditorGUILayout.TextField(input);

        GUILayout.Space(10);

        GUILayout.BeginHorizontal();
        if (GUILayout.Button("OK"))
        {
            onSubmit?.Invoke(input);
            Close();
        }
        if (GUILayout.Button("Cancel"))
        {
            Close();
        }
        GUILayout.EndHorizontal();
    }
}
