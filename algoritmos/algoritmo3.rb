# algoritmo3.rb  Aporte Integrante 3: Valentina Falconi
# ejercita: delimitadores, rangos, comentarios

# Funcion que saluda con un nombre (parametro opcional)
def saludar(nombre = "mundo")
  puts "Hola, #{nombre}!"
end

# Funcion que suma elementos de un arreglo
def sumar_elementos(arreglo)
  total = 0
  arreglo.each do |elemento|
    total = total + elemento
  end
  total
end

# Funcion que filtra valores dentro de un rango inclusivo
def en_rango_inclusivo(valores, inicio, fin_rango)
  resultado = []
  valores.each do |v|
    if v >= inicio && v <= fin_rango
      resultado.push(v)
    end
  end
  resultado
end

# Funcion que filtra valores dentro de un rango exclusivo
def en_rango_exclusivo(valores, inicio, fin_rango)
  resultado = []
  valores.each do |v|
    if v >= inicio && v < fin_rango
      resultado.push(v)
    end
  end
  resultado
end

# --- Programa principal ---

# Uso de parentesis, coma y llamada a funcion
saludar("Valentina")
saludar()

# Uso de corchetes para definir arreglo
numeros = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Rango inclusivo con ..
rango_inclusivo = 1..10
puts "Rango inclusivo: #{rango_inclusivo}"

# Rango exclusivo con ...
rango_exclusivo = 1...10
puts "Rango exclusivo: #{rango_exclusivo}"

# Uso de each con rango inclusivo
puts "Numeros del 1 al 5 (inclusivo):"
(1..5).each do |n|
  puts n
end

# Uso de each con rango exclusivo
puts "Numeros del 1 al 5 (exclusivo del 5):"
(1...5).each do |n|
  puts n
end

# Uso de llaves para hash (diccionario)
persona = { nombre: "Valentina", edad: 21, ciudad: "Guayaquil" }
puts persona[:nombre]
puts persona[:ciudad]

# Uso de punto para acceder a metodos
texto = "hola mundo"
puts texto.upcase
puts texto.length

# Suma de elementos del arreglo
total = sumar_elementos(numeros)
puts "Suma total: #{total}"

# Filtros con rangos
dentro_inclusivo = en_rango_inclusivo(numeros, 3, 7)
puts "Dentro de 3..7: #{dentro_inclusivo}"

dentro_exclusivo = en_rango_exclusivo(numeros, 3, 7)
puts "Dentro de 3...7: #{dentro_exclusivo}"

# Uso de dos puntos como simbolo
etiqueta = :activo
puts "Estado: #{etiqueta}"

# Uso de punto y coma (separador de sentencias)
a = 10; b = 20; c = a + b
puts "a + b = #{c}"

# Uso de hash con arrow (=>)
colores = { "rojo" => 1, "azul" => 2, "verde" => 3 }
puts colores["rojo"]