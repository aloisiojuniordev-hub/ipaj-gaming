import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/layout/Layout";
import { Loading } from "./components/ui/Status";
import Home from "./pages/Home";

// Páginas secundárias carregadas sob demanda.
const Catalog = lazy(() => import("./pages/Catalog"));
const ProductDetails = lazy(() => import("./pages/ProductDetails"));
const Cart = lazy(() => import("./pages/Cart"));
const Checkout = lazy(() => import("./pages/Checkout"));
const Laboratory = lazy(() => import("./pages/Laboratory"));
const HowItWorks = lazy(() => import("./pages/HowItWorks"));
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const Profile = lazy(() => import("./pages/Profile"));

function NotFound() {
  return <><h1>Página não encontrada</h1><p className="muted">Verifique o endereço.</p></>;
}

export default function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="catalogo" element={<Catalog />} />
          <Route path="produto/:id" element={<ProductDetails />} />
          <Route path="carrinho" element={<Cart />} />
          <Route path="checkout" element={<Checkout />} />
          <Route path="laboratorio" element={<Laboratory />} />
          <Route path="como-funciona" element={<HowItWorks />} />
          <Route path="entrar" element={<Login />} />
          <Route path="cadastro" element={<Register />} />
          <Route path="perfil" element={<Profile />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
