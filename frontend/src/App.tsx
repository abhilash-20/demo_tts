// import { Hero } from './components/Hero';
// import { InputMethods } from './components/InputMethods';
// import { AudiobookLibrary } from './components/AudiobookLibrary';

// function App() {
//   return (
//     <div className="min-h-screen bg-gray-50">
//       <Hero />
//       <InputMethods />
//       <AudiobookLibrary />
//     </div>
//   );
// }

// export default App;



// import { Hero } from './components/Hero';
// import { InputMethods } from './components/InputMethods';
// import { AudiobookLibrary } from './components/AudiobookLibrary';

// function App() {
//   return (
//     <div className="min-h-screen bg-gray-50 flex">
      
//       {/* Left Sidebar */}
//       <aside className="w-80 border-r border-gray-200 bg-white overflow-y-auto">
//         <AudiobookLibrary />
//       </aside>

//       {/* Main Content */}
//       <main className="flex-1">
//         <Hero />
//         <InputMethods />
//       </main>

//     </div>
//   );
// }

// export default App;


import { Hero } from './components/Hero';
import { InputMethods } from './components/InputMethods';
import { AudiobookLibrary } from './components/AudiobookLibrary';

function App() {
  return (
    <div className="h-screen bg-gray-50 flex overflow-hidden">

      {/* Sidebar */}
      <aside className="w-96 bg-white border-r border-gray-200 flex flex-col">
        <div className="flex-1 overflow-y-auto">
          <AudiobookLibrary />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <Hero />
        <InputMethods />
      </main>

    </div>
  );
}

export default App;

