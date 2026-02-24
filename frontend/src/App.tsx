import { useEffect, useState, useRef, createContext, useContext } from 'react';
import axios from 'axios';
import { BrowserRouter, Routes, Route, Link, useParams, useNavigate, Navigate, Outlet } from 'react-router-dom';
import Editor, { OnMount } from '@monaco-editor/react';

// --- НАСТРОЙКИ AXIOS ---
axios.defaults.baseURL = 'http://127.0.0.1:8888';
axios.defaults.withCredentials = true;

axios.interceptors.request.use(config => {
  if ((config.method === 'post' || config.method === 'put' || config.method === 'delete') && !config.headers['X-CSRF-Token']) {
    const match = document.cookie.match(new RegExp('(^| )csrf_token=([^;]+)'));
    if (match) {
      config.headers['X-CSRF-Token'] = match[2];
    }
  }
  return config;
});

// --- ТИПЫ ---
interface Project {
  id: number;
  title: string;
  content: string;
}

interface User {
  id: number;
  login: string;
}

interface AuthContextType {
  user: User | null;
  login: (userData: User) => void;
  logout: () => void;
}

// --- AUTH CONTEXT ---
const AuthContext = createContext<AuthContextType>(null!);

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });

  const login = (userData: User) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
    axios.post('/api/auth/logout').catch(console.error);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

const useAuth = () => useContext(AuthContext);

// --- КОМПОНЕНТЫ АВТОРИЗАЦИИ ---
function AuthForm({ isRegister = false }: { isRegister?: boolean }) {
  const [loginVal, setLoginVal] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      if (isRegister) {
        await axios.post('/api/auth/register', { login: loginVal, password });
        navigate('/login');
        alert('Успешно! Теперь войдите.');
      } else {
        const res = await axios.post('/api/auth/login', { login: loginVal, password });
        login(res.data.user);
        navigate('/');
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Ошибка сервера');
    }
  };

  return (
    <div style={styles.authContainer}>
      <form onSubmit={handleSubmit} style={styles.authForm}>
        <h2>{isRegister ? 'Регистрация' : 'Вход'}</h2>
        {error && <div style={{ color: '#ff6b6b', marginBottom: 10 }}>{error}</div>}

        <input
          type="text"
          placeholder="Логин"
          value={loginVal}
          onChange={e => setLoginVal(e.target.value)}
          style={styles.input}
          required
        />
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={e => setPassword(e.target.value)}
          style={styles.input}
          required
        />

        <button type="submit" style={styles.button}>
          {isRegister ? 'Создать аккаунт' : 'Войти'}
        </button>

        <div style={{ marginTop: 15, fontSize: '0.9em' }}>
          {isRegister ? (
            <span>Есть аккаунт? <Link to="/login" style={styles.link}>Войти</Link></span>
          ) : (
            <span>Нет аккаунта? <Link to="/register" style={styles.link}>Регистрация</Link></span>
          )}
        </div>
      </form>
    </div>
  );
}

// --- ЗАЩИТА МАРШРУТОВ ---
function ProtectedRoute() {
  const { user } = useAuth();
  return user ? <Outlet /> : <Navigate to="/login" />;
}

function Layout() {
  const { user, logout } = useAuth();
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header style={styles.header}>
        <div style={{ fontWeight: 'bold', fontSize: '1.2em' }}>CodeShare</div>
        <div>
          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
              <span>👤 {user.login}</span>
              <button onClick={logout} style={styles.smallBtn}>Выйти</button>
            </div>
          )}
        </div>
      </header>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <Outlet />
      </div>
    </div>
  );
}

// --- ОСНОВНЫЕ КОМПОНЕНТЫ ---
function MainList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const { logout } = useAuth();

  useEffect(() => {
    axios.get('/api/projects')
      .then(res => setProjects(res.data))
      .catch(err => {
        console.error(err);
        if (err.response?.status === 401) {
            logout(); // Защита: если кука протухла, принудительно выкидываем
        }
      });
  }, []);

  const createProject = async () => {
    try {
      const res = await axios.post('/api/projects', {
        title: `Новый проект ${projects.length + 1}`,
        content: "# Напишите ваш код здесь\n"
      });
      setProjects([res.data, ...projects]);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ padding: '20px', color: '#eee', overflowY: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Доступные проекты</h2>
        <button onClick={createProject} style={styles.button}>+ Создать новый</button>
      </div>

      {projects.length === 0 ? (
        <p style={{ color: '#aaa' }}>У вас пока нет проектов. Создайте первый!</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0, display: 'grid', gap: '10px', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
          {projects.map(p => (
            <li key={p.id} style={styles.listItem}>
              <Link to={`/projects/${p.id}`} style={styles.projectLink}>
                {p.title}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Detailed() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const editorRef = useRef<any>(null);
  const websocket = useRef<WebSocket | null>(null);
  const isRemoteUpdate = useRef(false);

  const handleEditorDidMount: OnMount = (editor) => {
    editorRef.current = editor;
  };

  // Замени старый handleShare на этот:
  const handleShare = async () => {
    const userToShare = prompt("Введите логин пользователя для доступа:");

    // Если нажали "Отмена" или ввели пустую строку — ничего не делаем
    if (!userToShare) return;

    try {
      await axios.post(`/api/projects/${id}/share`, {
        login: userToShare,
        role: 'editor' // По умолчанию даем права на редактирование. Можно поменять на 'viewer'
      });
      alert(`Пользователь ${userToShare} успешно добавлен в проект!`);
    } catch (e: any) {
      console.error(e);
      // Выводим конкретную ошибку от бэкенда (404, 403, 400) или стандартную
      const errorMessage = e.response?.data?.detail || 'Ошибка при добавлении пользователя';
      alert(`Ошибка: ${errorMessage}`);
    }
  };

  useEffect(() => {
    let isMounted = true;

    const setup = async () => {
      try {
        const resp = await axios.get(`/api/projects/${id}`);
        if (!isMounted) return;
        setProject(resp.data);

        const ws = new WebSocket(`ws://127.0.0.1:8888/ws/${id}`);

        ws.onopen = () => console.log("WS Connected");

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          const incomingChanges = data.changes || data;

          if (Array.isArray(incomingChanges) && editorRef.current) {
            isRemoteUpdate.current = true;
            editorRef.current.getModel().applyEdits(incomingChanges.map((edit: any) => ({
              ...edit,
              forceMoveMarkers: true
            })));
            setTimeout(() => { isRemoteUpdate.current = false; }, 0);
          }
        };

        websocket.current = ws;

      } catch (e: any) {
        console.error("Ошибка загрузки:", e);
        // Защита от чужих проектов
        if (e.response?.status === 403 || e.response?.status === 404) {
          alert("У вас нет доступа к этому проекту или он не существует");
          navigate('/');
        }
      }
    };

    setup();

    return () => {
      isMounted = false;
      websocket.current?.close();
    };
  }, [id, navigate]);

  const handleEditorChange = (value: string | undefined, event: any) => {
    if (isRemoteUpdate.current) return;
    if (websocket.current?.readyState === WebSocket.OPEN && event.changes) {
      const payload = JSON.stringify({ changes: event.changes });
      websocket.current.send(payload);
    }
  };

  if (!project) return <div style={{color: 'white', padding: '20px'}}>Загрузка...</div>;

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '10px 20px', background: '#252526', color: '#ccc', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #3e3e42' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <span style={{ fontWeight: 'bold' }}>📄 {project.title}</span>
          <button onClick={handleShare} style={{...styles.smallBtn, background: '#0e639c'}}>🤝 Поделиться</button>
        </div>
        <Link to="/" style={{ color: '#aaa', textDecoration: 'none', fontSize: '1.2em' }}>✕</Link>
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
            minimap: { enabled: false }
          }}
        />
      </div>
    </div>
  );
}

// --- APP & STYLES ---
export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <style>{`
          body, html, #root { margin: 0; padding: 0; height: 100%; background: #1e1e1e; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
          * { box-sizing: border-box; }
        `}</style>

        <Routes>
          <Route path="/login" element={<AuthForm />} />
          <Route path="/register" element={<AuthForm isRegister />} />

          <Route element={<ProtectedRoute />}>
             <Route element={<Layout />}>
                <Route path="/" element={<MainList />} />
                <Route path="/projects/:id" element={<Detailed />} />
             </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
  header: {
    padding: '12px 20px',
    background: '#007acc',
    color: 'white',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    boxShadow: '0 2px 5px rgba(0,0,0,0.2)'
  },
  authContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    color: '#eee'
  },
  authForm: {
    background: '#252526',
    padding: '40px',
    borderRadius: '10px',
    width: '350px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
    display: 'flex',
    flexDirection: 'column'
  },
  input: {
    padding: '12px',
    marginBottom: '15px',
    borderRadius: '6px',
    border: '1px solid #3e3e42',
    background: '#3c3c3c',
    color: 'white',
    fontSize: '15px',
    outline: 'none'
  },
  button: {
    padding: '12px',
    cursor: 'pointer',
    background: '#0e639c',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '15px',
    fontWeight: 'bold',
    transition: 'background 0.2s'
  },
  smallBtn: {
    padding: '6px 12px',
    cursor: 'pointer',
    background: 'rgba(255,255,255,0.15)',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    transition: 'background 0.2s'
  },
  link: {
    color: '#3794ff',
    textDecoration: 'none'
  },
  listItem: {
    border: '1px solid #3e3e42',
    padding: '20px',
    borderRadius: '8px',
    background: '#252526',
    transition: 'transform 0.1s, background 0.2s',
    cursor: 'pointer'
  },
  projectLink: {
    color: '#4fc1ff',
    textDecoration: 'none',
    fontSize: '18px',
    fontWeight: '600',
    display: 'block'
  }
};