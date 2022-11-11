public class something {
    public static void main(String[] args){
        Integer[] nums = {1,2,3,4,5,6,7,8};
        Node<Integer> first = null;
        for(int i=0; i<nums.length; i++)
            insertAtTail(nums[i], first);

        Node<Integer> cur = first;
        for(int i=0; i<nums.length; i++){
            System.out.println(cur.getData());
            cur = cur.getNext();
        }
    }

    public static void insertAtHead(Integer data, Node<Integer> head){
        if(head == null)
            head = new Node<Integer>(data, null);
        else{
            Node<Integer> first = new Node<Integer>(data, head);
            head = first;
        }
    }

    public static void insertAtTail(Integer data, Node<Integer> cur){
        if(cur == null)
            insertAtHead(data, cur);
        else if(cur.getNext() == null)
            cur.setNext(new Node<Integer>(data, null));
        else
            insertAtTail(data, cur.getNext());
    }
}

class Node<T> {
    private T data;
    private Node<T> next;

    public Node(T data, Node<T> next){
        this.data = data;
        this.next = next;
    }

    public T getData() {
        return data;
    }
    public Node<T> getNext() {
        return next;
    }
    public void setData(T data) {
        this.data = data;
    }
    public void setNext(Node<T> next) {
        this.next = next;
    }
}