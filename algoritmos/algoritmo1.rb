# algoritmo1.rb — Aporte Integrante 1: Annabella Sánchez
# Ejercita: variables, tipos primitivos, Array, if/elsif/else, función con retorno

# --- Constante ---
MAX_NOTA = 10

# --- Variable global ---
$escuela = "ESPOL"

# --- Función con parámetro y retorno ---
def calificar(nota, max = MAX_NOTA)
  porcentaje = (nota.to_f / max) * 100

  if porcentaje >= 90
    return "Excelente"
  elsif porcentaje >= 70
    return "Aprobado"
  elsif porcentaje >= 50
    return "Suficiente"
  else
    return "Reprobado"
  end
end

# --- Tipos primitivos ---
nombre   = "Annabella"
edad     = 21
promedio = 9.5
activo   = true
dato     = nil
estado   = :matriculado

# --- Variable de instancia (usada dentro de contexto de clase simplificado) ---
@carrera = "Ingeniería en Ciencias de la Computación"

# --- Array con distintos tipos ---
info_estudiante = [nombre, edad, promedio, activo, dato, estado]

# --- Recorrer el Array ---
info_estudiante.each do |elemento|
  if elemento.nil?
    puts "Valor: nil"
  else
    puts "Valor: #{elemento}"
  end
end

# --- Usar la función ---
notas = [10, 8, 6, 4, 9]
notas.each do |n|
  resultado = calificar(n)
  puts "Nota #{n}/#{MAX_NOTA} → #{resultado}"
end

puts "Escuela: #{$escuela}"
puts "Carrera: #{@carrera}"
