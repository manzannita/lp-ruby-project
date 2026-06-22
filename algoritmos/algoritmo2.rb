# algoritmo2.rb — Aporte Integrante 2: Cristian Intriago
# Ejercita: operadores aritméticos, asignación compuesta, comparación, lógicos, Hash y while

contador = 0
acumulador = 10
resultado = 0
base = 2
exponente = 3

datos = {
  "a" => 5,
  "b" => 3,
  "c" => 8
}

while contador < 4 && acumulador >= 0
  suma = datos["a"] + datos["b"]
  resta = datos["c"] - contador
  producto = suma * base
  division = producto / (contador + 1)
  modulo = acumulador % 3
  potencia = base ** exponente

  resultado += suma
  resultado -= contador
  resultado *= 2
  resultado /= 3

  if suma == 8 && resta != 0 || !(division > 10)
    puts "Iteración #{contador}: #{resultado}, #{division}, #{modulo}, #{potencia}"
  end

  contador += 1
  acumulador -= 2
end

if resultado <= 100 && resultado >= 0
  puts "Resultado final: #{resultado}"
else
  puts "Resultado fuera de rango"
end