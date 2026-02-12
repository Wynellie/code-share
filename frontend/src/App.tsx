import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { BrowserRouter, Routes, Route, Link, useParams, useNavigate } from 'react-router-dom';
import Editor, { OnMount } from '@monaco-editor/react';

interface Project {
  id: number;
  title: string;
  content: string;
}

function MainList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const navigate = useNavigate();

  // Загрузка списка
  useEffect(() => {
    axios.get('http://127.0.0.1:8888/api/projects')
      .then(res => setProjects(res.data))
      .catch(err => console.error(err));
  }, []);

  // Создание нового проекта 
  const createProject = async () => {
    try {
      const res = await axios.post('http://127.0.0.1:8888/api/projects', {
        title: `Project ${projects.length + 1}`,
        content: "print('Hello World')\n"
      });
      setProjects([res.data, ...projects]);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ padding: '20px', color: '#eee' }}>
      <h2>Все проекты</h2>
      <button onClick={createProject} style={{ padding: '10px', marginBottom: '20px', cursor: 'pointer' }}>
        + Создать новый
      </button>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {projects.map(p => (
          <li key={p.id} style={{ margin: '10px 0', border: '1px solid #444', padding: '10px', borderRadius: '5px' }}>
            <Link to={`/projects/${p.id}`} style={{ color: '#61dafb', textDecoration: 'none', fontSize: '18px' }}>
              {p.title} 
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Detailed() {
  const { id } = useParams();
  const [project, setProject] = useState<Project | null>(null);
  
  // Ссылки на объекты, не зависят от рендеров React
  const editorRef = useRef<any>(null);
  const websocket = useRef<WebSocket | null>(null);
  
  // true - мы сейчас применяем правки с сервера, и не надо слать их обратно.
  const isRemoteUpdate = useRef(false);

  // Когда Monaco загрузился, сохраняем ссылку
  const handleEditorDidMount: OnMount = (editor) => {
    editorRef.current = editor;
  };

  useEffect(() => {
    let isMounted = true;

    const setup = async () => {
      try {
        const resp = await axios.get(`http://127.0.0.1:8888/api/projects/${id}`);
        if (!isMounted) return;
        setProject(resp.data);

        const ws = new WebSocket(`ws://127.0.0.1:8888/ws/${id}`);

        ws.onopen = () => console.log("WS Connected");
        
        ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  // Достаем массив изменений: либо data.changes, либо сам data
  const incomingChanges = data.changes || data;

  if (Array.isArray(incomingChanges) && editorRef.current) {
    console.log("Применяю изменения:", incomingChanges);
    
    isRemoteUpdate.current = true;
    
    editorRef.current.getModel().applyEdits(incomingChanges.map((edit: any) => ({
      ...edit,
      forceMoveMarkers: true // Чтобы курсор не "зажевало" при вставке текста
    })));
    
    // Сбрасываем флаг в конце очереди событий
    setTimeout(() => { isRemoteUpdate.current = false; }, 0);
  }
};

        websocket.current = ws;

      } catch (e) {
        console.error("Ошибка загрузки:", e);
      }
    };

    setup();

    return () => {
      isMounted = false;
      websocket.current?.close();
    };
  }, [id]);

  // Обработка ввода пользователя
  const handleEditorChange = (value: string | undefined, event: any) => {
    // вызвано сервером - выходим
    if (isRemoteUpdate.current) return;

    if (websocket.current?.readyState === WebSocket.OPEN && event.changes) {
      // бэк ждет  { "changes": [...] }
      const payload = JSON.stringify({ changes: event.changes });
      websocket.current.send(payload);
    }
  };

  if (!project) return <div style={{color: 'white', padding: '20px'}}>Загрузка...</div>;

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '10px', background: '#333', color: 'white', display: 'flex', justifyContent: 'space-between' }}>
        <span>Project: {project.title}</span>
        <Link to="/" style={{ color: '#aaa' }}>Назад к списку</Link>
      </div>
      <div style={{ flex: 1 }}>
        <Editor
          height="100%"
          theme="vs-dark"
          defaultLanguage="python"
          defaultValue={project.content}
          onMount={handleEditorDidMount}
          onChange={handleEditorChange}
          options={{
            automaticLayout: true,
            fontSize: 16,
          }}
        />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <style>{`
        body, html, #root { margin: 0; padding: 0; height: 100%; background: #1e1e1e; }
        * { box-sizing: border-box; }
      `}</style>
      
      <Routes>
        <Route path="/" element={<MainList />} />
        <Route path="/projects/:id" element={<Detailed />} />
      </Routes>
    </BrowserRouter>
  );
}