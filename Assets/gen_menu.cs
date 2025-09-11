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
using Unity.EditorCoroutines.Editor; // <--- make sure you have this

using System;

public class MenuTest : EditorWindow
{

    static string prompt_buffer;
    
    [MenuItem("Gen/LoadAndCorrect")]
    static void LoadDialogue()
    {
        string path = EditorUtility.OpenFilePanel(
            "Select a scene to load",   // window title
            "Assets/Scenes",
            "unity");                    // extension filter (e.g. "txt", "png", "json"; empty = all files)

        Debug.Log("Opening scene at path " + path);
        Load(path, false, 0);
    }
    
    [MenuItem("Gen/LoadAndCycle")]
    static void LoadDialogueAndCycle()
    {
        string path = EditorUtility.OpenFilePanel(
            "Select a scene to load",   // window title
            "Assets/Scenes",
            "unity");                    // extension filter (e.g. "txt", "png", "json"; empty = all files)

        Debug.Log("Opening scene at path " + path);
        Load(path, true, 0);
    }
    
    static void Load(string path, bool cycle, int i)
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
            Debug.Log("Console cleared!");
            
            Debug.Log("Catching warnings...");
            ConsoleUtils.ClearConsole();
            
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
                    if (cycle == true)
                    {
                        var flaskObjForLoadingErrors = new GameObject("FlaskInterface");
                        var flaskWait = flaskObjForLoadingErrors.AddComponent<FlaskInterface>();
                        EditorCoroutineUtility.StartCoroutineOwnerless(WaitAndLoad(flaskWait, true, i));
                    }
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
        OpenPromptDialogue(false);
    }
    
    [MenuItem("Gen/PromptAndLoad")]
    static void PromptAndLoad()
    {
        OpenPromptDialogue(true); // Sets prompt_buffer
        var flaskObj = new GameObject("FlaskInterface");
        var flask = flaskObj.AddComponent<FlaskInterface>();
        EditorCoroutineUtility.StartCoroutineOwnerless(WaitAndLoad(flask, false, 0));
    }
    
    [MenuItem("Gen/PromptAndCycle %g")]
    static void PromptAndCycle()
    {
        OpenPromptDialogue(true); // Sets prompt_buffer
        var flaskObj = new GameObject("FlaskInterface");
        var flask = flaskObj.AddComponent<FlaskInterface>();
        EditorCoroutineUtility.StartCoroutineOwnerless(WaitAndLoad(flask, true, 0));
    }
    
    static IEnumerator WaitAndLoad(FlaskInterface flask, bool cycle, int i)
    {
        Debug.Log("Waiting for iteration number " + i.ToString()); 
        // Wait until Flask is done
        yield return flask.WaitOnFlask();

        // Now it’s safe to load
        Debug.Log("Should load only if WaitOnFlask returns...");
        Load("Assets/Scenes/last.unity", cycle, i + 1); // Yes, cycle
        Debug.Log("Flask ready, file loaded.");
    }
    
    static void OpenPromptDialogue(bool make_last)
    {
        TextInputDialog.Show("Enter text:", input =>
        {
            Debug.Log("User entered: " + input);
            prompt_buffer = input;
            var flaskObj = new GameObject("FlaskInterface");
            var flask = flaskObj.AddComponent<FlaskInterface>();
            flask.SendPromptToFlask(prompt_buffer, make_last);
            Debug.Log("Prompt `" + prompt_buffer + "` sent with make_last = " + make_last.ToString());
            UnityEngine.Object.DestroyImmediate(flask.gameObject);
        });
        
    }
    
    [MenuItem("Gen/Stop All Flask Interfaces")]
    static void StopAllFlaskInterfaces()
    {
        // Find all FlaskInterface components in the scene or editor
        FlaskInterface[] allFlasks = UnityEngine.Object.FindObjectsByType<FlaskInterface>(FindObjectsSortMode.None);

        if (allFlasks.Length == 0)
        {
            Debug.Log("No FlaskInterface objects found.");
            return;
        }

        foreach (var flask in allFlasks)
        {
            // Stop all coroutines on this FlaskInterface
            flask.StopAllCoroutines();

            // Optionally do any cleanup in FlaskInterface here
            // flask.OnStop(); // if you have a custom method

            // Delete the GameObject
            UnityEngine.Object.DestroyImmediate(flask.gameObject);
        }

        Debug.Log($"Stopped and deleted {allFlasks.Length} FlaskInterface object(s).");
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
        public void SendPromptToFlask(string prompt, bool make_last)
        {
            StartCoroutine(this.PromptToFlask(prompt, make_last));
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
        
        IEnumerator PromptToFlask(string prompt, bool make_last)
        {
            WWWForm form = new WWWForm();
            form.AddField("prompt", prompt);
            form.AddField("make_last", make_last.ToString());
            Debug.Log("Sending " + make_last.ToString() + " to Flask");
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
        
        public IEnumerator WaitOnFlask()
        {
            Debug.Log("In WaitOnFlask");

            string response = "";
            do
            {
                using (UnityWebRequest www = UnityWebRequest.Get("http://localhost:5000/wait"))
                {
                    yield return www.SendWebRequest();

                    if (www.result != UnityWebRequest.Result.Success)
                    {
                        Debug.LogError(www.error);
                        yield break; // Stop if network error
                    }

                    response = www.downloadHandler.text;
                }

                if (response == "last_not_ready")
                {
                    Debug.Log("Waiting for Flask...");
                    yield return new EditorWaitForSeconds(3f); // safely wait 3 seconds in editor
                }

            } while (response == "last_not_ready");
            // Otherwise, response is the number of correction iterations that have occured
            Debug.Log("File is ready. Not 'last_not_ready':" + response);
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

public static class ConsoleUtils
{
    public static void ClearConsole()
    {
        // Get the internal Unity class
        Assembly assembly = Assembly.GetAssembly(typeof(SceneView));
        Type logEntries = assembly.GetType("UnityEditor.LogEntries");

        // Call the Clear method
        MethodInfo clearMethod = logEntries.GetMethod("Clear", BindingFlags.Static | BindingFlags.Public);
        clearMethod.Invoke(null, null);
    }
}
