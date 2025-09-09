using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.UIElements;
using UnityEditor.UIElements;
using System.Collections.Generic;
using UnityEngine.Networking;
using System.Collections;
using System.Threading;
using System.Reflection;

using System;

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

            Debug.Log("Waiting for warnings to manifest.");

            
            try
            {
                Debug.Log("Opening scene: " + path);
                EditorSceneManager.OpenScene(path);
                Debug.Log("Done opening scene.");
            }
            // warnings are caught here by the warningCatcher
            catch (Exception ex)
            {
                Debug.Log("Errors caught.");
                // Capture everything into one string
                string errorDetails = $"Exception: {ex.Message}\n\nStack Trace:\n{ex.StackTrace}";

                // Log to Unity console
                Debug.LogError(errorDetails);
            }
            
            Debug.Log("Catching warnings...");
            EditorApplication.delayCall += () =>
            {
                List<string> messages = GetEditorConsoleLogs();

                if (messages.Count > 0)
                {
                    var flaskObj = new GameObject("FlaskInterface");
                    var flask = flaskObj.AddComponent<FlaskInterface>();
                    flask.SendErrorsToFlask(path, string.Join("\n\n", messages));
                    UnityEngine.Object.DestroyImmediate(flaskObj);
                    Debug.Log("Warnings sent.");
                }
                else
                {
                    Debug.Log("No warnings manifest.");
                }
            };

            
        }    
        else
        {
            Debug.Log("No scene selected.");
        }
    }

    public static List<string> GetEditorConsoleLogs()
    {
        var logs = new List<string>();
        Assembly editorAssembly = typeof(Editor).Assembly;
        Type logEntriesType = editorAssembly.GetType("UnityEditor.LogEntries");
        Type logEntryType = editorAssembly.GetType("UnityEditor.LogEntry");

        MethodInfo getCount = logEntriesType.GetMethod("GetCount", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
        MethodInfo getEntryInternal = logEntriesType.GetMethod("GetEntryInternal", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);

        int count = (int)getCount.Invoke(null, null);

        object logEntry = Activator.CreateInstance(logEntryType);

        for (int i = 0; i < count; i++)
        {
            // Pass row index and logEntry object
            getEntryInternal.Invoke(null, new object[] { i, logEntry });

            var binding = BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.Instance;
            

            string message = logEntryType.GetField("message", binding).GetValue(logEntry) as string;
            string file = logEntryType.GetField("file", binding).GetValue(logEntry) as string;
            int line = (int)logEntryType.GetField("line", binding).GetValue(logEntry);

            logs.Add($"[{file}:{line}] {message}");
        }

        return logs;
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
        UnityEngine.Object.DestroyImmediate(flask.gameObject);
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
            UnityEngine.Object.DestroyImmediate(flask.gameObject);
        });
        
    }
    
    [MenuItem("Gen/Do Something")]
    static void DoSomething()
    {
        Debug.Log("Sends Scene to VR or something...");
    }
}
/*
public class WarningCatcher : MonoBehaviour
{
    public List<string> logMessages = new List<string>();
    
    void OnEnable()
    {
        Application.logMessageReceived += HandleLog;
    }

    void OnDisable()
    {
        Application.logMessageReceived -= HandleLog;
    }

    public void HandleLog(string logString, string stackTrace, LogType type)
    {
        if (type == LogType.Warning)
        {
            string entry = $"[{type}] {logString}\n{stackTrace}";
            logMessages.Add(entry);
        }
    }
    
    public List<string> GetLogsAndClear()
    {
        var copy = new List<string>(logMessages);
        logMessages.Clear();
        return copy;
    }
}
*/
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
        
        public void SendErrorsToFlask(string path, string errorDetails)
        {
            StartCoroutine(this.ErrorsToFlask(path, errorDetails));
        }
        
        IEnumerator ErrorsToFlask(string path, string errors)
        {
            WWWForm form = new WWWForm();
            form.AddField("path", path);
            form.AddField("errors", errors);

            using UnityWebRequest www = UnityWebRequest.Post("http://localhost:5000/errors", form);
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
                    Debug.Log("System failed to accept errors.");
                    Debug.Log(response);
                }
            }
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
