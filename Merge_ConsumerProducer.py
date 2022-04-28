"""

Celia Vaquero
Version corregida

Tenemos NPROD procesos que producen numeros no negativos de forma
creciente. Se consume el menor de los numeros producidos en el almacen
y se anade a una lista llamada merge. Una vez consumido un numero podemos
volver a producir en esa posicion del almacen, producimos generando un numero
aleatorio entre 0 y 5 su sumandole el numero anterior del almacen, asi todos
los numeros producidos seran mayores que los consumidos anteriormente.
Cuando un proceso acaba de producir,ya que solo se produce N veces, produce
un -1, de esta forma sabemos que en esa posicion del alamacen ya no podemos
consumir.


Otra forma de plantearlo habria sido definiendo la lista running como una
lista compartida y pasarla como argumento tambien en el productor.
De esta manera la lista se actualizaria inmediatamente despues de la asignacion
storage[pid] = -1 haciendo: running[pid] = False. 
Asi no habria que comprobar en consumer si se ha anadido un nuevo -1 en cada
vuelta del bucle. Todo funcionaria igual.

"""

from multiprocessing import Process, Manager
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Array
import random


N = 200
K = 1
NPROD = 3
NCONS = 1

#N=20
#NPROD = 30


def add_data(storage, pid, mutex):
    mutex.acquire()
    try:
        storage[pid] = storage[pid] + random.randint(0,5)
    finally:
        mutex.release()
  
#funcion que devuelve el minimo del almacen y la posicion en la que se encuentra
#ya que necesitamos saber que parte del almacen se ha quedado vacio para saber
#que proceso debe producir
def get_minimo(storage, mutex, running):
    mutex.acquire()
    try:
        valores = []
        for i in range(NPROD):
            if running[i]:
                valores.append(storage[i])
        minimo = min(valores)
        almacen = list(storage)
    finally:
        mutex.release()
    return minimo,almacen.index(minimo)

#cuando el productor acaba de producir anade un -1
def producer(storage, empty, non_empty, mutex, merge):
    pid = int(current_process().name.split('_')[1])#indice asociado al productor
    for i in range(N):
        print (f"prod {pid} produciendo")
        empty.acquire() #esperamos a que el valor anterior haya sido consumido para poder producir
        add_data(storage, pid, mutex) #anadimos el valor que produzcamos al almacen
        non_empty.release() #avisamos de que ya se ha producido y por tanto se puede consumir en esa posicion
        print(list(storage))
        print(f"prod {pid} almacenando")
    
    #esperamos a haber consumido el ultimo elemento producido y producimos un -1 en esa posicion
    empty.acquire()
    storage[pid]= -1
    
    #avisamos de que ya hemos producido el nuevo valor en esa posicion
    non_empty.release()


def consumer(storage, empty, non_empty, mutex, merge):
    for i in range(NPROD):
        non_empty[i].acquire() #esperamos en todas las posiciones a que se haya producido
    #definimos la lista running para saber en que posiciones del almacen no podemos consumir por que hay un -1
    running = [True]*NPROD
    while True in running:
        #obtenemos el minimo del almacen en m
        #en j almacenamos el indice del minimo para dar permiso al productor de esa posicion a producir
        
        m,j = get_minimo(storage, mutex,running) 
        merge.append(m) #almacenamos el minimo en merge
        print (f"consumiendo {m} en pos {j}")
        empty[j].release() #damos permiso al proceso j para producir
        non_empty[j].acquire() #esperamos a que se produzca otro valor para no consumir el mismo
        
        #ya se ha producido en esa posicion por lo que comprobamos si se ha anadido un -1 al almacen
        #en caso afirmativo actualizamos la lista running
        for i in range(NPROD):
            if storage[i] == -1:
                running[i] = False
          
    print("Ya no se puede consumir")
    print("\nmerge:",list(merge))




def main():
    storage = Array('i', NPROD*K) #almacen donde porduciremos los enteros
    print ("almacen inicial", storage[:])
    
    #creamos una lista de semaforos, empty[i] sera el semaforo del proceso i
    empty = [0]*NPROD
    non_empty = [0]*NPROD
    for i in range(NPROD):
        empty[i] = BoundedSemaphore(K)
        non_empty[i] = Semaphore(0)
    
    mutex = Lock()
    
    manager = Manager()
    merge = manager.list() #lista  del resultado, enteros ordenados de forma creciente
    
    prodlst = [ Process(target=producer,
                        name=f'prod_{i}',
                        args=(storage, empty[i], non_empty[i], mutex, merge))
                for i in range(NPROD) ]

    conslst = [Process(target=consumer,
                      name="cons_{i}",
                      args=(storage, empty, non_empty, mutex, merge))]

    for p in prodlst + conslst:
        p.start()

    for p in prodlst + conslst:
        p.join()
    
   
if __name__ == '__main__':
    main()
