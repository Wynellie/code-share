import { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';

interface Project {
  id: number;
  title: string;
  content: string;
}

export default function EditorPage() {
  const [project, setProject] = useState<Project | null>(null);
  const [code, setCode] = useState("");

  // Загружаем конкретный проект (например, с ID 2, который ты создал)
  useEffect(() => {
    axios.get<Project>(`http://127.0.0.1:8888/api/projects/2`) // Пока захардкодим ID
      .then(res => {
        setProject(res.data);
        setCode(res.data.content);
      });
  }, []);

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) setCode(value);
  };

  const saveCode = async () => {
    if (!project) return;
    try {
      await axios.put(`http://127.0.0.1:8888/api/projects/${project.id}`, {
        title: project.title,
        content: code
      });
      alert("Сохранено!");
    } catch (e) {
      console.error("Ошибка сохранения", e);
    }
  };

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "10px", background: "#202124", color: "white", display: "flex", justifyContent: "space-between" }}>
        <span>{project?.title || "Загрузка..."}</span>
        <button onClick={saveCode} style={{ cursor: "pointer" }}>Сохранить (Ctrl+S)</button>
      </div>
      
      <Editor
        height="100%"
        defaultLanguage="python"
        theme="vs-dark"
        value={code}
        onChange={handleEditorChange}
        options={{
          fontSize: 16,
          minimap: { enabled: false },
          automaticLayout: true,
        }}
      />
    </div>
  );
}