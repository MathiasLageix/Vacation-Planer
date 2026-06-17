import { SearchForm } from "./components/SearchForm";

export default function Home() {
  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">
          Planifiez votre voyage
        </h1>
        <p className="text-slate-500">
          Recherche en temps réel · Insights de prix · Deep links vers les plateformes d'achat
        </p>
      </div>
      <SearchForm />
    </div>
  );
}
