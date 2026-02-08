import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import {BrowserRouter, Routes, Route, Link, useParams} from 'react-router-dom'
import Editor from '@monaco-editor/react';

interface Project{
  id: number
  title: string
  content: string
}
function Detailed(){
  // хуй-то его пойми, как этот useParams работает

  const {id} = useParams();
  const [project, setProject] = useState<Project>();
  const websocket = useRef<WebSocket | null>(null)

  useEffect(() => {
    let isMounted = true; 

    const setup = async () => {
      const resp = await axios.get(`http://127.0.0.1:8888/api/projects/${id}`);
      setProject(resp.data)

      if (!project) return;

      websocket.current = new WebSocket(`ws://127.0.0.1:8888/ws/${resp.data?.id}`)
      websocket.current.onmessage = (event) => {
      setProject(prev => prev ? { ...prev, content: event.data } : prev);
    };
    }

    setup();

    return () => {
    isMounted = false;
    websocket.current?.close();
  };
  }, [id])

  const handleEditorChange = (value: string | undefined, event: any) => {
    websocket.current?.send(JSON.stringify(event.changes));
  }

  return (
    <div style={{ flex: 1, height: '100vh', position: 'relative' }}>
      <Editor
        height="100%" // Теперь он займет всю высоту контейнера
        theme="vs-dark"
        defaultLanguage="python"
        value={project?.content}
        onChange={handleEditorChange}
      />
    </div>
  )
}

function MainList(){
  const [projects, setProjects] = useState<Array<Project>>([])

  useEffect(() => {
    const callAPI = async () => {
      const resp = await axios.get('http://127.0.0.1:8888/api/projects/');

      setProjects(resp.data);
      
    }

    callAPI();

  }, [])

  return (
    <>
      <ul>
        {projects.map((project) => {
          return <li key = {project.id}>{<Link to = {`/projects/${project.id}`}>{project.title}</Link>}</li>
          })}
      </ul> 
    </>
  )
}

export default function App() {

  

  return (
      <BrowserRouter>
      <div style={{ display: 'flex', width: '100vw', height: '100vh' }}>
        <nav style={{ width: '250px', borderRight: '1px solid #333', overflowY: 'auto' }}>
          <MainList />
        </nav>
        <div style={{ flex: 1 }}>
          <Routes>
            <Route path="/" element={<div>Выберите проект</div>} />
            <Route path="/projects/:id" element={<Detailed />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}